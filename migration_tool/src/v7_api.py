# import os

# from rich.console import Console
from darwin.client import Client
from typing import Union, List
import supervisely as sly
from darwin.exceptions import InvalidLogin, NameTaken
from darwin.dataset.remote_dataset_v2 import RemoteDatasetV2

import migration_tool.src.globals as g

# console = Console()

# API_KEY = "JUFxKUH.wfjargM-xR4-L3wR2kkZaxFM-AqTiZWs"
# TEAM_NAME = "tkotteam001"
# EXPORT_NAME = "export_2"
# SAVE_PATH = "data.zip"
# DATASET_DIR = "datasets"
# os.makedirs(DATASET_DIR, exist_ok=True)


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

    print(dir(datasets[0]))
    return datasets


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
