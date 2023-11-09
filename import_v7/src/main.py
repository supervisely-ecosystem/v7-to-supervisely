import os
from typing import List
import supervisely as sly

import globals as g
from converters import process_v7_dataset


IMAGES_DIR = "images"
RELEASES_DIR = "releases"


@sly.handle_exceptions
def main():
    sly.logger.debug("Starting main function...")
    data_path = download_data()

    project_name = f"From V7 {os.path.basename(data_path)}"
    sly.logger.info(f"Will use project name: {project_name}")

    images_projects = []
    videos_projects = []

    sly.logger.info(f"Will process V7 directories in {data_path}...")

    for v7_directory in v7_directories(data_path):
        sly.logger.info(f"Found V7 directory: {v7_directory}, will process it...")
        try:
            image_project_info, video_project_info = process_v7_dataset(
                v7_directory, g.api, g.WORKSPACE_ID
            )

            if image_project_info:
                sly.logger.info(
                    f"Created images project {image_project_info.name}, ID: {image_project_info.id}"
                )
                images_projects.append(image_project_info)
            if video_project_info:
                sly.logger.info(
                    f"Created videos project {video_project_info.name}, ID: {video_project_info.id}"
                )
                videos_projects.append(video_project_info)
        except Exception as e:
            sly.logger.warning(
                f"Error while processing V7 directory: {e}, "
                "please, check that you provided a valid V7 dataset."
            )

    sly.logger.info(f"Finished processing V7 directories in {data_path}.")

    if images_projects:
        images_project_names = [project.name for project in images_projects]
        images_project_ids = [project.id for project in images_projects]
        sly.logger.info(
            f"Created following images projects: {images_project_names} with IDs: {images_project_ids}"
        )
    if videos_projects:
        videos_project_names = [project.name for project in videos_projects]
        videos_project_ids = [project.id for project in videos_projects]
        sly.logger.info(
            f"Created following videos projects: {videos_project_names} with IDs: {videos_project_ids}"
        )

    if not images_projects and not videos_projects:
        sly.logger.warning(
            "No projects were created. Please, check that you provided a valid V7 dataset."
        )

    sly.logger.info("App finished work.")


def v7_directories(data_path: str) -> [List[str]]:
    sly.logger.debug(f"Looking for V7 directories in {data_path}...")

    images_dir = os.path.join(data_path, IMAGES_DIR)
    releases_dir = os.path.join(data_path, RELEASES_DIR)

    if os.path.isdir(images_dir) and os.path.isdir(releases_dir):
        sly.logger.info(f"Found V7 dataset in {data_path}")
        return [data_path]

    subdirs = [
        os.path.join(data_path, subdir) for subdir in sly.fs.get_subdirs(data_path)
    ]
    v7_subdirs = []
    for subdir in subdirs:
        if os.path.isdir(os.path.join(subdir, IMAGES_DIR)) and os.path.isdir(
            os.path.join(subdir, RELEASES_DIR)
        ):
            v7_subdirs.append(subdir)

    sly.logger.info(f"Found V7 directories: {v7_subdirs}")
    return v7_subdirs if v7_subdirs else []


def download_data() -> str:
    sly.logger.info("Starting download data...")
    if g.SLY_FILE:
        sly.logger.info(f"Was provided a path to file: {g.SLY_FILE}")
        data_path = _download_archive(g.SLY_FILE)

    elif g.SLY_FOLDER:
        sly.logger.info(f"Was provided a path to folder: {g.SLY_FOLDER}")
        files_list = g.api.file.list(g.TEAM_ID, g.SLY_FOLDER)
        if len(files_list) == 1:
            sly.logger.debug(
                f"Provided folder contains only one file: {files_list[0].name}. "
                "Will handle it as an archive."
            )
            data_path = _download_archive(files_list[0].path)
        else:
            sly.logger.debug(
                f"Provided folder contains more than one file: {files_list}. "
                "Will handle it as a folder with unpacked CVAT data."
            )

            data_path = _download_folder(g.SLY_FOLDER)

    sly.logger.debug(f"Data downloaded and prepared in {data_path}.")

    return data_path


def _download_folder(remote_path: str) -> str:
    sly.logger.info(f"Starting download folder from {remote_path}...")
    folder_name = sly.fs.get_file_name(remote_path)
    save_path = os.path.join(g.UNPACKED_DIR, folder_name)
    sly.logger.debug(f"Will download folder to {save_path}.")
    g.api.file.download_directory(g.TEAM_ID, remote_path, save_path)
    sly.logger.debug(f"Folder downloaded to {save_path}.")
    return save_path


def _download_archive(remote_path: str) -> str:
    sly.logger.info(f"Starting download archive from {remote_path}...")
    archive_name = sly.fs.get_file_name_with_ext(remote_path)
    save_path = os.path.join(g.ARCHIVE_DIR, archive_name)
    sly.logger.debug(f"Will download archive to {save_path}.")
    g.api.file.download(g.TEAM_ID, remote_path, save_path)
    sly.logger.debug(f"Archive downloaded to {save_path}.")

    file_name = sly.fs.get_file_name(remote_path)
    unpack_path = os.path.join(g.UNPACKED_DIR, file_name)
    sly.logger.debug(f"Will unpack archive to {unpack_path}.")
    try:
        sly.fs.unpack_archive(save_path, unpack_path)
    except Exception as e:
        raise RuntimeError(
            f"Can't unpack archive from {remote_path}. "
            f"Provided file must be a valid archive. {e}"
        )
    sly.logger.debug(f"Archive unpacked to {unpack_path}.")
    return unpack_path


if __name__ == "__main__":
    main()
