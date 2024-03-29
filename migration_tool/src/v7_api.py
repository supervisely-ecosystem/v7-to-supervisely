import os
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
        client.set_datasets_dir(g.DOWNLOAD_DIR)
        sly.logger.debug(f"Datasets dir set to: {g.DOWNLOAD_DIR}")
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


def retreive_dataset(dataset: RemoteDatasetV2) -> bool:
    export_name = get_export_name()
    sly.logger.info(f"Will try to export dataset {dataset.name} to {export_name}")
    try:
        dataset: RemoteDatasetV2
        dataset.export(export_name)
        sly.logger.info(
            f"Export {export_name} created successfully, it may take a while "
            "before the export will be available for download."
        )
    except NameTaken:
        sly.logger.info(f"Export {export_name} already exists")
    finally:
        try:
            release = dataset.get_release()
            sly.logger.info("Release was retreived successfully.")
            sly.logger.info(f"Image count: {release.image_count}")
            dataset.pull(release=release, multi_threaded=False, use_folders=True)

            export_path = get_export_path(dataset)
            sly.logger.info(f"Export path of dataset {dataset.name}: {export_path}")
            if not os.path.isdir(export_path):
                sly.logger.info(f"Can't find downloaded dataset in {export_path}")
                return False
            return True
        except NotFound:
            sly.logger.warning(f"Can't find any release for dataset {dataset.name}")
            return False
        except ValueError as e:
            sly.logger.warning(
                f"Can not download the dataset {dataset.name} due to V7 API or SDK error. "
                "This error comes from V7 and is not related to Supervisely. "
                "Please, contact V7 support about it. "
                f"Error: {e}"
            )
            return False


def get_export_name():
    timestamp = datetime.now().strftime("%Y-%m-%d")
    return f"sly_export_{timestamp}"


def get_export_path(dataset: RemoteDatasetV2) -> str:
    # ! Darwin CLI lowers the dataset and team names, while pulling the dataset
    # which causes the issue, when the dataset could not be found on Linux.
    # It may be fixed in the next releases, so check it while updating dependencies.
    dataset_name = dataset.name.lower()
    team_name = dataset.team.lower()
    # ! These variables added here only for bringing the attention to the issue.
    # And can be removed in the future, if Darwin CLI will be fixed.
    return os.path.join(g.DOWNLOAD_DIR, team_name, dataset_name)
