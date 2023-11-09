import supervisely as sly
from typing import Union
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
from migration_tool.src.v7_api import (
    get_datasets,
    get_dataset_url,
    retreive_dataset,
    get_export_path,
)
from import_v7.src.converters import process_v7_dataset
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
        export_path = get_export_path(dataset)
        sly.logger.info(f"Export path for dataset {dataset.name}: {export_path}")
        download_status = retreive_dataset(dataset)
        if not download_status:
            sly.logger.info(
                f"Can not download dataset data from V7 API for dataset {dataset.name}"
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
                return save_dataset(dataset, retry)
            else:
                # If the archive is empty after 10 retries, return False.
                sly.logger.warning(
                    f"Can't download dataset {dataset.name} after 10 retries."
                )
                return
        else:
            sly.logger.debug(f"Dataset {dataset.name} was downloaded.")
            return export_path

    succesfully_uploaded = 0
    uploded_with_errors = 0

    with copying_progress(
        total=len(g.STATE.selected_datasets), message="Copying..."
    ) as pbar:
        for dataset_id in g.STATE.selected_datasets:
            if not g.STATE.continue_copying:
                sly.logger.debug("Copying is stopped by the user.")
                break

            dataset = g.STATE.datasets[dataset_id]
            sly.logger.debug(
                f"Copying project with id: {dataset_id} and name: {dataset.name}"
            )
            update_cells(dataset_id, new_status=g.COPYING_STATUS.working)

            dataset_path = save_dataset(dataset)
            if dataset_path is None:
                sly.logger.warning(f"Can not download dataset {dataset.name}.")
                pbar.update(1)
                continue

            image_project_info, video_project_info = process_v7_dataset(
                dataset_path, g.api, g.STATE.selected_workspace
            )

            if image_project_info is not None or video_project_info is not None:
                new_status = g.COPYING_STATUS.copied
                succesfully_uploaded += 1
                update_cells(dataset_id, new_status=new_status)

            if image_project_info is not None:
                try:
                    new_url = sly.utils.abs_url(image_project_info.url)
                except Exception:
                    new_url = image_project_info.url
                sly.logger.debug(f"New URL for images project: {new_url}")
                update_cells(dataset_id, new_url=new_url)
            if video_project_info is not None:
                try:
                    new_url = sly.utils.abs_url(video_project_info.url)
                except Exception:
                    new_url = video_project_info.url
                sly.logger.debug(f"New URL for videos project: {new_url}")
                update_cells(dataset_id, new_url=new_url)

            pbar.update(1)

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

    sly.logger.info(
        f"Removed content from {g.DOWNLOAD_DIR}, will stop the application."
    )

    from migration_tool.src.main import app

    app.stop()


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
