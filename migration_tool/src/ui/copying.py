import os
import shutil
import supervisely as sly
from typing import List, Tuple, Union
from time import sleep
from darwin.dataset.remote_dataset_v2 import RemoteDatasetV2
from supervisely.app.widgets import (
    Container,
    Card,
    Table,
    Button,
    Progress,
    Text,
    Flexbox,
)
import xml.etree.ElementTree as ET
from migration_tool.src.v7_api import get_datasets, get_dataset_url, retreive_dataset

# from import_cvat.src.converters import (
#     convert_images_annotations,
#     convert_video_annotations,
#     prepare_images_for_upload,
#     upload_images_task,
#     update_project_meta,
#     images_to_mp4,
# )
import migration_tool.src.globals as g


COLUMNS = [
    "COPYING STATUS",
    "ID",
    "NAME",
    "ITEM COUNT",
    "V7 URL",
    "SUPERVISELY URL",
]

datasets_table = Table(fixed_cols=3, per_page=20, sort_column_id=1)
datasets_table.hide()

copy_button = Button("Copy", icon="zmdi zmdi-copy")
stop_button = Button("Stop", icon="zmdi zmdi-stop", button_type="danger")
stop_button.hide()

buttons_flexbox = Flexbox([copy_button, stop_button])

copying_progress = Progress()
good_results = Text(status="success")
bad_results = Text(status="error")
good_results.hide()
bad_results.hide()

card = Card(
    title="3️⃣ Copying",
    description="Copy selected datasets from V7 to Supervisely.",
    content=Container(
        [datasets_table, buttons_flexbox, copying_progress, good_results, bad_results]
    ),
    collapsable=True,
)
card.lock()
card.collapse()


def build_datasets_table() -> None:
    """Fills the table with datasets from V7.
    Uses global g.STATE.selected_datasets to get the list of datasets to show.
    g.STATE.selected_datasets is a list of dataset IDs from V7.
    """
    sly.logger.debug("Building datasets table...")
    datasets_table.loading = True
    rows = []

    for dataset in get_datasets():
        dataset: RemoteDatasetV2
        if dataset.dataset_id in g.STATE.selected_datasets:
            dataset_url = get_dataset_url(dataset.dataset_id)
            rows.append(
                [
                    g.COPYING_STATUS.waiting,
                    dataset.dataset_id,
                    dataset.name,
                    dataset.item_count,
                    f'<a href="{dataset_url}" target="_blank">{dataset_url}</a>',
                    "",
                ]
            )

    sly.logger.debug(f"Prepared {len(rows)} rows for the projects table.")

    datasets_table.read_json(
        {
            "columns": COLUMNS,
            "data": rows,
        }
    )

    datasets_table.loading = False
    datasets_table.show()

    sly.logger.debug("Datasets table is built.")


@copy_button.click
def start_copying() -> None:
    """Main function for copying projects from V7 to Supervisely.
    1. Starts copying progress, changes state of widgets in UI.
    2. Iterates over selected projects from V7.
    3. For each project:
        3.1. Updates the status in the projects table to "Copying...".
        3.2. Iterates over tasks in the project.
        3.3. For each task:
            3.3.1. Downloads the task data from V7 API.
            3.3.2. Saves the task data to the zip archive (using up to 10 retries).
        3.4. If the archive is empty after 10 retries, updates the status in the projects table to "Error".
        3.5. Otherwise converts the task data to Supervisely format and uploads it to Supervisely.
        3.6. If the task was uploaded with errors, updates the status in the projects table to "Error".
        3.7. Otherwise updates the status in the projects table to "Copied".
    4. Updates the status in the projects table to "Copied" or "Error" for each project.
    5. Stops copying progress, changes state of widgets in UI.
    6. Shows the results of copying.
    7. Removes content from download and upload directories (if not in development mode).
    8. Stops the application (if not in development mode).
    """
    sly.logger.debug(
        f"Copying button is clicked. Selected datasets: {g.STATE.selected_datasets}"
    )

    stop_button.show()
    copy_button.text = "Copying..."
    g.STATE.continue_copying = True

    def save_dataset(dataset: RemoteDatasetV2, retry: int = 0) -> Union[None, str]:
        sly.logger.info("Trying to retreive dataset data from V7 API...")
        archive_path = retreive_dataset(dataset)
        if archive_path is None:
            sly.logger.info(
                f"Can not retreive dataset data from V7 API for dataset {dataset.name}"
            )
            sly.logger.info(
                f"Will retry to download dataset {dataset.name}, because the archive is empty."
            )
            if retry < 10:
                # Try to download the task data again.
                retry += 1
                timer = 5
                while timer > 0:
                    sly.logger.info(f"Retry {retry} in {timer} seconds...")
                    sleep(1)
                    timer -= 1

                sly.logger.info(f"Retry {retry} to download dataset {dataset.name}...")
                save_dataset(dataset, retry)
            else:
                # If the archive is empty after 10 retries, return False.
                sly.logger.warning(
                    f"Can't download dataset {dataset.name} after 10 retries."
                )
                return
        else:
            sly.logger.debug(f"Archive for dataset {dataset.name} was downloaded.")
            return archive_path

    succesfully_uploaded = 0
    uploded_with_errors = 0

    with copying_progress(
        total=len(g.STATE.selected_datasets), message="Copying..."
    ) as pbar:
        for dataset_id in g.STATE.selected_datasets:
            dataset = g.STATE.datasets[dataset_id]
            sly.logger.debug(
                f"Copying project with id: {dataset_id} and name: {dataset.name}"
            )
            update_cells(dataset_id, new_status=g.COPYING_STATUS.working)

            archive_path = save_dataset(dataset)
            if not archive_path:
                pass

            # task_ids_with_errors = []
            # task_archive_paths = []

            # for task in cvat_data(project_id=project_id):
            #     data_type = task.data_type

            #     sly.logger.debug(
            #         f"Copying task with id: {task.id}, data type: {data_type}"
            #     )
            #     if not g.STATE.continue_copying:
            #         sly.logger.debug("Copying is stopped by the user.")
            #         continue

            #     project_name = g.STATE.project_names[project_id]
            #     project_dir = os.path.join(
            #         g.ARCHIVE_DIR, f"{project_id}_{project_name}_{data_type}"
            #     )
            #     sly.fs.mkdir(project_dir)
            #     task_filename = f"{task.id}_{task.name}_{data_type}.zip"

            #     task_path = os.path.join(project_dir, task_filename)
            #     download_status = save_task_to_zip(task.id, task_path)
            #     if download_status is False:
            #         task_ids_with_errors.append(task.id)
            #     else:
            #         task_archive_paths.append((task_path, data_type))

            # if not task_archive_paths:
            #     sly.logger.warning(
            #         f"No tasks was successfully downloaded for project ID {project_id}. It will be skipped."
            #     )
            #     new_status = g.COPYING_STATUS.error
            #     uploded_with_errors += 1
            # else:
            #     upload_status = convert_and_upload(
            #         project_id, project_name, task_archive_paths
            #     )

            #     if task_ids_with_errors:
            #         sly.logger.warning(
            #             f"Project ID {project_id} was downloaded with errors. "
            #             "Task IDs with errors: {task_ids_with_errors}."
            #         )
            #         new_status = g.COPYING_STATUS.error
            #         uploded_with_errors += 1
            #     elif not upload_status:
            #         sly.logger.warning(
            #             f"Project ID {project_id} was uploaded with errors."
            #         )
            #         new_status = g.COPYING_STATUS.error
            #         uploded_with_errors += 1
            #     else:
            #         sly.logger.info(
            #             f"Project ID {project_id} was downloaded successfully."
            #         )
            #         new_status = g.COPYING_STATUS.copied
            #         succesfully_uploaded += 1

            # update_cells(project_id, new_status=new_status)

            # sly.logger.info(f"Finished processing project ID {project_id}.")

            # pbar.update(1)

    if succesfully_uploaded:
        good_results.text = f"Succesfully uploaded {succesfully_uploaded} projects."
        good_results.show()
    if uploded_with_errors:
        bad_results.text = f"Uploaded {uploded_with_errors} projects with errors."
        bad_results.show()

    copy_button.text = "Copy"
    stop_button.hide()

    sly.logger.info(f"Finished copying {len(g.STATE.selected_datasets)} projects.")

    if sly.is_development():
        # * For debug purposes it's better to save the data from V7.
        sly.logger.debug(
            "Development mode, will not stop the application. "
            "And NOT clean download and upload directories."
        )
        return

    sly.fs.clean_dir(g.DOWNLOAD_DIR)
    sly.fs.clean_dir(g.PREPARED_DIR)

    sly.logger.info(
        f"Removed content from {g.DOWNLOAD_DIR} and {g.PREPARED_DIR}."
        "Will stop the application."
    )

    from migration_tool.src.main import app

    app.stop()


def convert_and_upload(
    project_id: id, project_name: str, task_archive_paths: List[Tuple[str, str]]
) -> bool:
    """Unpacks the task archive, parses it's content, converts it to Supervisely format
    and uploads it to Supervisely.

    1. Checks if the task archive contains images or video.
    2. Creates projects with corresponding data types in Supervisely (images or videos).
    3. For each task:
        3.1. Unpacks the task archive in a separate directory in project directory.
        3.2. Parses annotations.xml and reads list of images.
        3.3. Converts V7 annotations to Supervisely format.
        3.4. Depending on data type (images or video) creates specific annotations.
        3.5. Uploads images or video to Supervisely.
        3.6. Uploads annotations to Supervisely.
    4. Updates the project in the projects table with new URLs.
    5. Returns True if the upload was successful, False otherwise.

    :param project_id: ID of the project in V7
    :type project_id: id
    :param project_name: name of the project in V7
    :type project_name: str
    :param task_archive_paths: list of tuples for each task, which containing path to the task archive and data type
        possible data types: 'imageset', 'video'
    :type task_archive_paths: List[Tuple[str, str]]
    :return: status of the upload (True if the upload was successful, False otherwise)
    :rtype: bool
    """
    unpacked_project_path = os.path.join(g.UNPACKED_DIR, f"{project_id}_{project_name}")
    sly.logger.debug(f"Unpacked project path: {unpacked_project_path}")

    images_project = None
    videos_project = None

    if any(task_data_type == "imageset" for _, task_data_type in task_archive_paths):
        images_project = g.api.project.create(
            g.STATE.selected_workspace,
            f"From CVAT {project_name} (images)",
            change_name_if_conflict=True,
        )
        sly.logger.debug(f"Created project {images_project.name} in Supervisely.")

        images_project_meta = sly.ProjectMeta.from_json(
            g.api.project.get_meta(images_project.id)
        )

        sly.logger.debug(f"Retrieved images project meta for {images_project.name}.")

    if any(task_data_type == "video" for _, task_data_type in task_archive_paths):
        videos_project = g.api.project.create(
            g.STATE.selected_workspace,
            f"From CVAT {project_name} (videos)",
            type=sly.ProjectType.VIDEOS,
            change_name_if_conflict=True,
        )
        sly.logger.debug(f"Created project {videos_project.name} in Supervisely.")

        videos_project_meta = sly.ProjectMeta.from_json(
            g.api.project.get_meta(videos_project.id)
        )

        sly.logger.debug(f"Retrieved videos project meta for {videos_project.name}.")

    succesfully_uploaded = True

    for task_archive_path, task_data_type in task_archive_paths:
        sly.logger.debug(
            f"Processing task archive {task_archive_path} with data type {task_data_type}."
        )
        # * Unpacking archive, parsing annotations.xml and reading list of images.
        images_et, images_paths, source = unpack_and_read_task(
            task_archive_path, unpacked_project_path
        )

        sly.logger.debug(f"Parsed annotations and found {len(images_et)} images.")

        # * Using archive name as dataset name.
        dataset_name = sly.fs.get_file_name(task_archive_path)
        sly.logger.debug(f"Will use {dataset_name} as dataset name.")

        if task_data_type == "imageset":
            # Working with Supervisely Images Project.
            sly.logger.debug(
                "Data type is imageset, will convert annotations to Supervisely format."
            )

            task_tags, image_objects = convert_images_annotations(
                images_et, images_paths
            )

            # * Prepare lists of paths, names and build annotations from labels.
            images_names, images_paths, images_anns = prepare_images_for_upload(
                g.api, image_objects, images_project, images_project_meta
            )

            sly.logger.debug(f"Task data type is {task_data_type}, will upload images.")

            upload_images_task(
                g.api,
                dataset_name,
                images_project,
                images_names,
                images_paths,
                images_anns,
                task_tags,
            )

            sly.logger.info(
                f"Finished processing task archive {task_archive_path} with data type {task_data_type}."
            )
        elif task_data_type == "video":
            # Working with Supervisely Videos Project.
            sly.logger.debug(
                "Task data type is video, will convert annotations to Supervisely format."
            )

            (
                video_size,
                video_frames,
                video_objects,
                video_tags,
            ) = convert_video_annotations(images_et, images_paths)

            sly.logger.debug(f"Found {len(video_frames)} frames in the video.")

            update_project_meta(
                g.api,
                videos_project_meta,
                videos_project.id,
                labels=video_objects,
                tags=video_tags,
            )

            # Prepare the name for output video using source name from CVAT annotation.
            # Prepare the path for output video using project directory and source name.
            # Save the video to the path.
            source_name = f"{sly.fs.get_file_name(source)}.mp4"
            video_path = os.path.join(unpacked_project_path, source_name)
            sly.logger.debug(f"Will save video to {video_path}.")
            images_to_mp4(video_path, images_paths, video_size)

            # Create Supervisely VideoAnnotation object using data from CVAT annotation.
            frames = sly.FrameCollection(video_frames)
            objects = sly.VideoObjectCollection(video_objects)
            tag_collection = sly.VideoTagCollection(video_tags)

            sly.logger.debug(
                f"Will create VideoAnnotation object with: {video_size} size, "
                f"{len(frames)} frames, {len(objects)} objects, {len(tag_collection)} tags."
            )

            ann = sly.VideoAnnotation(
                video_size, len(frames), objects, frames, tag_collection
            )

            sly.logger.debug("VideoAnnotation successfully created.")

            dataset_info = g.api.dataset.create(
                videos_project.id, dataset_name, change_name_if_conflict=True
            )

            sly.logger.debug(
                f"Created dataset {dataset_info.name} in project {videos_project.name}."
                "Uploading video..."
            )

            uploaded_video: sly.api.video_api.VideoInfo = g.api.video.upload_path(
                dataset_info.id, source_name, video_path
            )

            sly.logger.debug(
                f"Uploaded video {source_name} to dataset {dataset_info.name}."
            )

            g.api.video.annotation.append(uploaded_video.id, ann)

            sly.logger.debug(f"Added annotation to video with ID {uploaded_video.id}.")

            sly.logger.info(
                f"Finished processing task archive {task_archive_path} with data type {task_data_type}."
            )

    sly.logger.info(
        f"Finished copying project {project_name} from CVAT to Supervisely."
    )

    if images_project:
        try:
            new_url = sly.utils.abs_url(images_project.url)
        except Exception:
            new_url = images_project.url
        sly.logger.debug(f"New URL for images project: {new_url}")
        update_cells(project_id, new_url=new_url)
    if videos_project:
        try:
            new_url = sly.utils.abs_url(videos_project.url)
        except Exception:
            new_url = videos_project.url
        sly.logger.debug(f"New URL for videos project: {new_url}")
        update_cells(project_id, new_url=new_url)

    sly.logger.debug(f"Updated project {project_name} in the projects table.")

    return succesfully_uploaded


def unpack_and_read_task(
    task_archive_path: str, unpacked_project_path: str
) -> Tuple[List[ET.Element], List[str], str]:
    """Unpacks the task archive from CVAT and reads it's content.
    Parses annotations.xml and reads list of images in it.
    Reads contents of the images directory and prepares a list of paths to the images.
    Reads the "source" parameter in annotations.xml, it's needed to retrieve the
    original name of the video file in CVAT.

    :param task_archive_path: path to the task archive on the local machine
    :type task_archive_path: str
    :param unpacked_project_path: path to the directory where the task archive will be unpacked
    :type unpacked_project_path: str
    :return: list of images in annotations.xml, list of paths to the images, value of the "source" parameter
    :rtype: Tuple[List[ET.Element], List[str], str]
    """
    unpacked_task_dir = sly.fs.get_file_name(task_archive_path)
    unpacked_task_path = os.path.join(unpacked_project_path, unpacked_task_dir)

    sly.fs.unpack_archive(task_archive_path, unpacked_task_path, remove_junk=True)
    sly.logger.debug(f"Unpacked from {task_archive_path} to {unpacked_task_path}")

    images_dir = os.path.join(unpacked_task_path, "images")
    images_list = sly.fs.list_files(images_dir)

    sly.logger.debug(f"Found {len(images_list)} images in {images_dir}.")

    if not images_list:
        sly.logger.warning(f"No images found in {images_dir}, task will be skipped.")
        return

    annotations_xml_path = os.path.join(unpacked_task_path, "annotations.xml")
    if not os.path.exists(annotations_xml_path):
        sly.logger.warning(
            f"Can't find annotations.xml file in {unpacked_task_path}, will upload images without labels."
        )

    tree = ET.parse(annotations_xml_path)
    sly.logger.debug(f"Parsed annotations.xml from {annotations_xml_path}.")

    # * Getting source parameter, which nested in "meta" -> "task" -> "source".
    try:
        source = tree.find("meta").find("task").find("source").text
    except Exception:
        sly.logger.debug(f"Source parameter was not found in {annotations_xml_path}.")
        source = None

    images_et = tree.findall("image")
    sly.logger.debug(f"Found {len(images_et)} images in annotations.xml.")

    images_paths = [
        os.path.join(images_dir, image_et.attrib["name"]) for image_et in images_et
    ]

    return images_et, images_paths, source


def update_cells(project_id: int, **kwargs) -> None:
    """Updates cells in the projects table by project ID.
    Possible kwargs:
        - new_status: new status for the project
        - new_url: new Supervisely URL for the project

    :param project_id: project ID in CVAT for projects table to update
    :type project_id: int
    """
    key_cell_value = project_id
    key_column_name = "ID"
    if kwargs.get("new_status"):
        column_name = "COPYING STATUS"
        new_value = kwargs["new_status"]
    elif kwargs.get("new_url"):
        column_name = "SUPERVISELY URL"
        url = kwargs["new_url"]

        # When updating the cell with the URL we need to append the new URL to the old value
        # for cases when one CVAT project was converted to multiple Supervisely projects.
        # This usually happens when CVAT project contains both images and videos
        # while Supervisely supports one data type per project.
        old_value = get_cell_value(project_id)
        if old_value:
            old_value += "<br>"
        new_value = old_value + f"<a href='{url}' target='_blank'>{url}</a>"

    datasets_table.update_cell_value(
        key_column_name, key_cell_value, column_name, new_value
    )


def get_cell_value(
    project_id: int, column: str = "SUPERVISELY URL"
) -> Union[str, None]:
    """Returns value of the cell in the projects table by project ID and column name.
    By default returns value of the "SUPERVISELY URL" column.

    :param project_id: project ID in CVAT to find the table row
    :type project_id: int
    :param column: name of the columnm where to get the value, defaults to "SUPERVISELY URL"
    :type column: str, optional
    :return: value of the cell in the projects table or None if not found
    :rtype: Union[str, None]
    """
    table_json_data = datasets_table.get_json_data()["table_data"]

    # Find column index by column name.
    cell_column_idx = None
    for column_idx, column_name in enumerate(table_json_data["columns"]):
        if column_name == column:
            cell_column_idx = column_idx
            break

    for row_idx, row_content in enumerate(table_json_data["data"]):
        if row_content[1] == project_id:
            return row_content[cell_column_idx]


@stop_button.click
def stop_copying() -> None:
    """Stops copying process by setting continue_copying flag to False."""
    sly.logger.debug("Stop button is clicked.")

    g.STATE.continue_copying = False
    copy_button.text = "Stopping..."

    stop_button.hide()
