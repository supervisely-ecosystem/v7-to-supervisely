import os
from typing import List
import supervisely as sly


def get_entities_paths(dataset_path: str) -> List[str]:
    """Returns list of paths to entities in "images" directory of dataset in
    absolute format.

    :param dataset_path: path to dataset directory
    :type dataset_path: str
    :return: list of paths to entities
    :rtype: List[str]
    """
    sly.logger.info(f"Looking for entities in {dataset_path}")
    images_directory = os.path.join(dataset_path, "images")
    if not os.path.isdir(images_directory):
        return []

    entities_paths = [
        os.path.abspath(os.path.join(images_directory, entity_file))
        for entity_file in sly.fs.list_files(images_directory)
    ]
    sly.logger.info(f"Found {len(entities_paths)} entities.")
    sly.logger.debug(f"Entities paths: {entities_paths}")
    return entities_paths


def get_release_path(dataset_path: str) -> str:
    """Returns path to the latest release of dataset in absolute format.

    :param dataset_path: path to dataset directory
    :type dataset_path: str
    :return: path to the latest release of dataset
    :rtype: str
    """
    sly.logger.info(f"Looking for the latest release in {dataset_path}")
    releases_directory = os.path.join(dataset_path, "releases")
    releases = filter(
        lambda x: x.startswith("sly_export_"),
        sly.fs.get_subdirs(releases_directory),
    )
    releases = [
        os.path.abspath(os.path.join(releases_directory, release))
        for release in releases
    ]
    releases = sorted(releases, reverse=True)
    sly.logger.info(f"Found {len(releases)} releases, will use the latest one.")
    sly.logger.debug(f"Releases: {releases}. Latest release: {releases[0]}")
    return releases[0]


def get_ann_paths(entities_paths: List[str]) -> List[str]:
    """Returns list of paths to annotations in "annotations" directory of
    the latest release of dataset in absolute format.

    :param entities_paths: list of paths to entities
    :type entities_paths: List[str]
    :return: list of paths to annotations
    :rtype: List[str]
    """
    dataset_path = os.path.dirname(os.path.dirname(entities_paths[0]))
    sly.logger.info(f"Looking for annotations in {dataset_path}")
    latest_release_path = get_release_path(dataset_path)
    anns_directory = os.path.join(latest_release_path, "annotations")
    ann_paths = []
    for entity_path in entities_paths:
        entity_name = sly.fs.get_file_name(entity_path)
        ann_path = os.path.abspath(os.path.join(anns_directory, f"{entity_name}.json"))
        ann_paths.append(ann_path)
    sly.logger.info(f"Found {len(ann_paths)} annotations.")
    sly.logger.debug(f"Annotations paths: {ann_paths}")
    return ann_paths
