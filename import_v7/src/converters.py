import os
from typing import List, Tuple, Dict, Any, Union, Literal
import supervisely as sly
from supervisely.geometry.graph import KeypointsTemplate
import numpy as np


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


def split_entities(
    entities_paths: List[str], ann_paths: List[str]
) -> Tuple[List[str], List[str]]:
    """Splits entities into images and videos by its extensions.

    :param entities_paths: paths to entities (image or video files)
    :type entities_paths: List[str]
    :param ann_paths: paths to annotations
    :type ann_paths: List[str]
    :return: tuple of lists of paths to images and videos
    :rtype: Tuple[List[str], List[str]]
    """
    sly.logger.info(f"Splitting {len(entities_paths)} entities into images and videos")
    image_entities, video_entities = [], []
    for entity_path, ann_path in zip(entities_paths, ann_paths):
        ext = sly.fs.get_file_ext(entity_path)
        if sly.image.is_valid_ext(ext):
            image_entities.append((entity_path, ann_path))
        elif sly.video.is_valid_ext(ext):
            video_entities.append((entity_path, ann_path))
        else:
            sly.logger.warning(f"Unknown extension {ext} of entity {entity_path}")
    sly.logger.info(
        f"Splitting finished. Images: {len(image_entities)}, videos: {len(video_entities)}"
    )
    sly.logger.debug(
        f"Image entities: {image_entities}, video entities: {video_entities}"
    )
    return image_entities, video_entities


def convert_bbox(v7_label: Dict[str, Any]) -> sly.Label:
    # TODO: Video support + docstrings
    class_name = v7_label.get("name")
    bbox = v7_label.get("bounding_box")
    sly.logger.debug(f"Converting bbox: {bbox} with class name: {class_name}")

    obj_class = sly.ObjClass(name=class_name, geometry_type=sly.Rectangle)

    height, width = bbox.get("h"), bbox.get("w")
    x, y = bbox.get("x"), bbox.get("y")
    sly.logger.debug(f"height: {height}, width: {width}, x: {x}, y: {y}")

    bbox_coordinates = [height, width, x, y]
    if any([coord is None for coord in bbox_coordinates]):
        sly.logger.warning(f"Invalid bbox: {bbox} with class name: {class_name}")
        return None

    top, left = y, x
    bottom = top + height
    right = left + width

    geometry = sly.Rectangle(top=top, left=left, bottom=bottom, right=right)

    sly_label = sly.Label(obj_class=obj_class, geometry=geometry)

    return sly_label


def convert_polyline(v7_label: Dict[str, Any]) -> sly.Label:
    # TODO: Video support + docstrings
    class_name = v7_label.get("name")
    line = v7_label.get("line")
    sly.logger.debug(f"Converting polyline: {line} with class name: {class_name}")

    obj_class = sly.ObjClass(name=class_name, geometry_type=sly.Polyline)

    exterior = get_exterior(line.get("path"))

    geometry = sly.Polyline(exterior=exterior)

    sly_label = sly.Label(
        geometry=geometry,
        obj_class=obj_class,
    )

    return sly_label


def convert_polygon(v7_label: Dict[str, Any]) -> sly.Label:
    # TODO: Video support + docstrings
    class_name = v7_label.get("name")
    polygon = v7_label.get("polygon")
    sly.logger.debug(f"Converting polygon: {polygon} with class name: {class_name}")

    obj_class = sly.ObjClass(name=class_name, geometry_type=sly.Polygon)

    exterior = get_exterior(polygon.get("paths")[0])

    geometry = sly.Polygon(exterior=exterior)

    sly_label = sly.Label(
        geometry=geometry,
        obj_class=obj_class,
    )

    return sly_label


def convert_point(v7_label: Dict[str, Any]) -> sly.Label:
    # TODO: Video support + docstrings
    class_name = v7_label.get("name")
    keypoint = v7_label.get("keypoint")
    sly.logger.debug(f"Converting keypoint: {keypoint} with class name: {class_name}")

    obj_class = sly.ObjClass(name=class_name, geometry_type=sly.Point)
    row, col = keypoint.get("y"), keypoint.get("x")

    geometry = sly.Point(row=row, col=col)

    sly_label = sly.Label(
        geometry=geometry,
        obj_class=obj_class,
    )

    return sly_label


def convert_graph(v7_label: Dict[str, Any]) -> sly.Label:
    # TODO: Video support + docstrings
    class_name = v7_label.get("name")
    skeleton = v7_label.get("skeleton")
    nodes = skeleton.get("nodes")

    MULTIPLIER = 10

    template = KeypointsTemplate()
    sly_nodes = []
    for idx, node in enumerate(nodes):
        label = node.get("name")
        row, col = node.get("y"), node.get("x")
        template.add_point(label=label, row=idx * MULTIPLIER, col=idx * MULTIPLIER)
        sly_nodes.append(sly.Node(label=label, row=row, col=col))

    obj_class = sly.ObjClass(
        name=class_name,
        geometry_type=sly.GraphNodes,
        geometry_config=template,
    )

    geometry = sly.GraphNodes(sly_nodes)

    sly_label = sly.Label(geometry=geometry, obj_class=obj_class)

    return sly_label


def convert_bitmap(v7_label: Dict[str, Any], **kwargs) -> sly.Label:
    # TODO: Video support + docstrings
    height, width = kwargs.get("height"), kwargs.get("width")
    sly.logger.debug(f"Height: {height}, width: {width} for bitmap conversion")

    class_name = v7_label.get("name")
    obj_class = sly.ObjClass(name=class_name, geometry_type=sly.Bitmap)
    raster_layer = v7_label.get("raster_layer")
    dense_rle = raster_layer.get("dense_rle")
    sly.logger.debug(f"Converting bitmap: {dense_rle} with class name: {class_name}")

    binary_mask = dense_rle_to_binary_mask(dense_rle, height, width)

    geometry = sly.Bitmap(data=binary_mask)

    sly_label = sly.Label(
        geometry=geometry,
        obj_class=obj_class,
    )

    return sly_label


def dense_rle_to_binary_mask(rle: List[int], height: int, width: int) -> np.ndarray:
    """Converts dense RLE to binary mask.
    Dense RLE contains pairs of values: value and count of this value.
    RLE example: [0, 91830, 1, 1, 0, 181449]
        where pixels from 0 to 91830 are 0
        then 1 pixel is 1
        then pixels from 0 to 181449 are 0

    :param rle: mask in dense RLE format
    :type rle: List[int]
    :param height: height of mask (image)
    :type height: int
    :param width: width of mask (image)
    :type width: int
    :return: binary mask, contains 0 and 1 values
    :rtype: np.ndarray
    """
    decoded_rle = []
    for rle_pair in zip(rle[::2], rle[1::2]):
        value, count = rle_pair
        decoded_rle.extend([value] * count)
    binary_mask = np.array(decoded_rle).reshape((height, width))
    return binary_mask


def convert_tag(v7_label: Dict[str, Any]) -> sly.Tag:
    class_name = v7_label.get("name")
    tag_meta = sly.TagMeta(name=class_name, value_type=sly.TagValueType.NONE)
    return sly.Tag(tag_meta)


def get_exterior(path: List[Dict[str, float]]) -> List[Tuple[float, float]]:
    exterior = []
    for point in path:
        exterior.append((point.get("y"), point.get("x")))
    return exterior


def v7_image_ann_to_sly(v7_ann: Dict[str, Any], image_path: str) -> sly.Annotation:
    """Converts V7 annotation to Supervisely annotation for image.

    :param v7_ann: V7 annotation in JSON format
    :type v7_ann: Dict[str, Any]
    :param image_path: path to entity (image) to read its size if it is not in JSON
    :type image_path: str
    :return: Supervisely annotation object
    :rtype: sly.Annotation
    """
    try:
        slot = v7_ann.get("item").get("slots")[0]
        image_height, image_width = slot.get("height"), slot.get("width")
    except Exception as e:
        sly.logger.info(
            f"Can not get image size from annotation: {e}, will read it from entity."
        )
        image_height, image_width = sly.image.read(image_path).shape[:2]
    sly.logger.info(f"Image size (HxW): {image_height}x{image_width}")

    v7_labels = v7_ann.get("annotations", [])
    sly.logger.info(f"Found {len(v7_labels)} V7 labels in annotation.")
    sly.logger.debug(f"V7 Labels dict: {v7_labels}")

    sly_labels, img_tags = [], []
    for v7_label in v7_labels:
        geometry_type = get_geometry_type(v7_label)
        convert_func = CONVERT_MAP.get(geometry_type)
        if convert_func is None:
            sly.logger.warning(f"Can't find any know geometry type in {v7_label}")
            continue
        sly_label = convert_func(v7_label, height=image_height, width=image_width)
        if sly_label is not None:
            if geometry_type == "tag":
                img_tags.append(sly_label)
            else:
                sly_labels.append(sly_label)

    sly_ann = sly.Annotation(
        img_size=(image_height, image_width), labels=sly_labels, img_tags=img_tags
    )
    return sly_ann


def get_geometry_type(
    v7_label: Dict[str, Any]
) -> Literal["bounding_box", "line", "polygon"]:
    """Returns string with geometry type of V7 label.
    V7 dict labels are unordered, so we need to find geometry type key.

    :param v7_label: V7 label in JSON format
    :type v7_label: Dict[str, Any]
    :return: string with geometry type of V7 label
    :rtype: str
    """
    appeared_geometries = []
    for key in v7_label.keys():
        if key in CONVERT_MAP.keys():
            appeared_geometries.append(key)

    if len(appeared_geometries) > 1 and "bounding_box" in appeared_geometries:
        appeared_geometries.remove("bounding_box")
    elif len(appeared_geometries) == 0:
        return
    return appeared_geometries[0]


def process_v7_dataset(
    dataset_path: str, api: sly.Api, workspace_id: int
) -> Tuple[Union[sly.ProjectInfo, None], Union[sly.ProjectInfo, None]]:
    """Reads, converts and uploads dataset from V7 format to Supervisely format.
    Creating two projects: one for images and one for videos if there are
    corresponding entities in dataset.

    :param dataset_path: path to dataset directory in V7 format
    :type dataset_path: str
    :param api: Supervisely API object
    :type api: sly.Api
    :param workspace_id: ID of workspace to upload dataset in Supervisely
    :type workspace_id: int
    :return: tuple of projects info for images and videos
        or None if there are no corresponding entities
    :rtype: Tuple[Union[sly.ProjectInfo, None], Union[sly.ProjectInfo, None]]
    """
    dataset_name = os.path.basename(dataset_path)
    sly.logger.info(f"Processing dataset {dataset_name} from path {dataset_path}...")
    entities_paths = get_entities_paths(dataset_path)
    anns_paths = get_ann_paths(entities_paths)

    image_project_info = video_project_info = None

    image_entities, video_entities = split_entities(entities_paths, anns_paths)

    if len(image_entities) > 0:
        image_project_info = process_image_entities(
            image_entities, api, workspace_id, dataset_name
        )
    if len(video_entities) > 0:
        video_project_info = process_video_entities(
            video_entities, api, workspace_id, dataset_name
        )

    return image_project_info, video_project_info


def process_image_entities(
    image_entities: List[Tuple[str, str]],
    api: sly.Api,
    workspace_id: int,
    project_name: str,
):
    sly.logger.info(
        f"Starting processing project {project_name} with {len(image_entities)} images"
    )

    project_info = api.project.create(
        workspace_id,
        f"From V7 {project_name} (images)",
        type=sly.ProjectType.IMAGES,
        change_name_if_conflict=True,
    )
    sly.logger.debug(f"Created project {project_info.name} with ID {project_info.id}")
    dataset_info = api.dataset.create(
        project_info.id,
        "ds0",
        change_name_if_conflict=True,
    )
    sly.logger.debug(f"Created dataset {dataset_info.name} with ID {dataset_info.id}")

    project_meta = sly.ProjectMeta.from_json(api.project.get_meta(project_info.id))
    sly.logger.debug(f"Retrieved project meta: {project_meta}")

    sly_anns = []
    image_names = []
    image_paths = []
    for image_path, ann_path in image_entities:
        v7_ann = sly.json.load_json_file(ann_path)
        # ! Debug code, remove it later
        sly.json.dump_json_file(v7_ann, ann_path)
        # ! End of debug code
        sly_ann = v7_image_ann_to_sly(v7_ann, image_path)
        for img_tag in sly_ann.img_tags:
            if img_tag.meta not in project_meta.tag_metas:
                project_meta = project_meta.add_tag_meta(img_tag.meta)
                sly.logger.info(f"Added image tag {img_tag.meta.name} to project meta")
        for label in sly_ann.labels:
            if label.obj_class not in project_meta.obj_classes:
                project_meta = project_meta.add_obj_class(label.obj_class)
                sly.logger.info(
                    f"Added object class {label.obj_class.name} to project meta"
                )
        sly_anns.append(sly_ann)
        image_name = sly.fs.get_file_name_with_ext(image_path)
        image_names.append(image_name)
        image_paths.append(image_path)

    api.project.update_meta(project_info.id, project_meta)
    sly.logger.debug(f"Project {project_info.name} meta updated")

    image_infos = api.image.upload_paths(dataset_info.id, image_names, image_paths)
    sly.logger.info(
        f"Uploaded {len(image_infos)} images to project {project_info.name}"
    )
    image_ids = [image_info.id for image_info in image_infos]

    api.annotation.upload_anns(image_ids, sly_anns)
    sly.logger.info(
        f"Uploaded {len(sly_anns)} annotations to project {project_info.name}"
    )

    sly.logger.info(f"Finished processing project {project_info.name}")

    return project_info


def process_video_entities():
    pass


CONVERT_MAP = {
    "bounding_box": convert_bbox,
    "line": convert_polyline,
    "polygon": convert_polygon,
    "tag": convert_tag,
    "keypoint": convert_point,
    "skeleton": convert_graph,
    "raster_layer": convert_bitmap,
}
