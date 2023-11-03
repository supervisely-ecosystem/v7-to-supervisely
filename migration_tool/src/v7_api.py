from darwin.client import Client
from typing import Union, List
import supervisely as sly
from darwin.exceptions import InvalidLogin, NameTaken, NotFound
from datetime import datetime
from darwin.dataset.remote_dataset_v2 import RemoteDatasetV2

import migration_tool.src.globals as g


DEFAULT_DATASET_ADDRESS = "https://darwin.v7labs.com/datasets"


def get_configurtation() -> Union[None, Client]:
    try:
        client = Client.from_api_key(g.STATE.v7_api_key)
        sly.logger.debug("Successfully logged in V7 API.")
        client.set_datasets_dir(g.ARCHIVE_DIR)
        sly.logger.debug(f"Datasets dir set to: {g.ARCHIVE_DIR}")
        return client
    except InvalidLogin:
        sly.logger.error("Can not connect with provided API key.")
        return


def get_datasets() -> List[RemoteDatasetV2]:
    client = get_configurtation()
    if client is None:
        return
    datasets = []
    for dataset in client.list_remote_datasets():
        datasets.append(dataset)
    return datasets


def get_dataset_url(dataset_id: int) -> str:
    return f"{DEFAULT_DATASET_ADDRESS}/{dataset_id}/"


def retreive_dataset(dataset: RemoteDatasetV2) -> Union[None, str]:
    export_name = get_export_name()
    sly.logger.info(f"Will try to export dataset {dataset.name} to {export_name}")
    try:
        dataset.export(export_name)
        sly.logger.info(
            f"Export {export_name} created successfully, it may take a while "
            "before the export will be available for download."
        )
    except NameTaken:
        sly.logger.info(f"Export {get_export_name()} already exists")
    finally:
        try:
            release = dataset.get_release()
            sly.logger.info("Release was retreived successfully.")
            sly.logger.info(f"Image count: {release.image_count}")
            dataset.pull(release=release, multi_threaded=False, use_folders=True)

            return get_export_path()
        except NotFound:
            sly.logger.warning(f"Can't find any release for dataset {dataset.name}")
            return


def get_export_name():
    timestamp = datetime.now().strftime("%Y-%m-%d")
    return f"sly_export_{timestamp}"


def get_export_path():
    pass


# for dataset in client.list_remote_datasets():
#     # console.print(type(dataset))
#     # console.print(dir(dataset))

#     try:
#         dataset.export(EXPORT_NAME)
#     except NameTaken:
#         console.print(f"Export {EXPORT_NAME} already exists")
#         release = dataset.get_release()
#         console.print(f"Release: {release}")
#         console.print(f"Image count: {release.image_count}")

#         dataset.pull(release=release, multi_threaded=False, use_folders=True)
