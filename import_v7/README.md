<div align="center" markdown>
<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/118521851/281445527-06753d8e-85e6-4412-9eb6-6ca5b27ccd90.png"/>

# Convert and copy V7 dataset to Supervisely

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/v7-to-supervisely/import_v7)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/v7-to-supervisely)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/v7-to-supervisely/import_v7.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/v7-to-supervisely/import_v7.png)](https://supervise.ly)

</div>

## Overview

This application allows you convert images and videos with annotations from V7 format to Supervisely format using archive or folder with dataset in Darwin JSON Format format (`Darwin JSON Format` both for images and videos).<br>

\*️⃣ If you want to copy datasets directly from V7 instance you can use fully automated [V7 to Supervisely Migration Tool](https://ecosystem.supervisely.com/apps/v7-to-supervisely/migration_tool) app from Supervisely Ecosystem.<br>

## Preparation

First, you need to export your data from V7 referring to [this guide](https://docs.v7labs.com/docs/export-your-data-1). Learn more about Darwin JSON Format format in [official documentation](https://docs.v7labs.com/reference/darwin-json).<br>

You can download an example of data for import [here](https://github.com/supervisely-ecosystem/v7-to-supervisely/files/13298115/v7-dataset-example.zip).<br>
After exporting, ensure that you have the following structure of your data for running this app:

```text
📦 folder-with-dataset
┣ 📂 images
┣ 🏞️ car_001.jpeg
┣ 🏞️ car_002.jpeg
┗ 🏞️ car_003.jpeg
┣ 📂 releases
┃ ┣ 📂 release-name
┃ ┃ ┣ 📂 annotations
┃ ┃ ┃ ┣ 📄 car_001.json
┃ ┃ ┃ ┣ 📄 car_002.json
┃ ┃ ┃ ┣ 📄 car_003.json
```
ℹ️ NOTE: In Darwin JSON Format format, videos are also stored in the `images` folder.<br>

In output of this app you will receive the following structure on Supervisely platform:

```text
Project with images in Supervisely, containing one dataset with images and annotations:
📂 folder-with-dataset
┗ 📂 ds0
  ┣ 🏞️ car_001.jpeg
  ┣ 🏞️ car_002.jpeg
  ┗ 🏞️ car_003.jpeg
```

ℹ️ V7 datasets can contain both images and videos, but Supervisely project can contain only one type of data. If the V7 dataset contains both images and videos, the application will create two projects in Supervisely: one with images and one with videos.<br>

## How To Run

### Uploading an archive with projects in V7 format

**Step 1:** Run the app<br>

<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/118521851/281453664-5fd63cc0-3d3b-4e45-a1bf-f742bbe30845.png"/><br>

**Step 2:** Drag and drop the archive or select it in Team Files<br>

<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/118521851/281453677-8173ffcc-a2c5-4340-bd9c-e22724ca1104.png"/><br>

**Step 3:** Press the `Run` button<br>

### Uploading a folder with projects in V7 format

**Step 1:** Run the app<br>

**Step 2:** Drag and drop the folder or select it in Team Files<br>

<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/118521851/281453688-acbbb096-30c7-4026-adfc-1301638240ff.png"/><br>

**Step 3:** Press the `Run` button<br>

After completing the `Step 3️⃣`, the application will start converting and copying your projects to Supervisely, after completing the process the application will automatically stops.<br>

ℹ️ Currently conversion of Cuboid geometry is not supported, corresponding annotations will be skipped.<br>
ℹ️ Supervisely doesn't support Ellipse geometry, this kind of labels will be skipped.<br>

## Acknowledgement

- [darwin-py github](https://github.com/v7labs/darwin-py) ![GitHub Org's stars](https://img.shields.io/github/stars/v7labs/darwin-py?style=social)
- [V7 documentation](https://docs.v7labs.com/)
