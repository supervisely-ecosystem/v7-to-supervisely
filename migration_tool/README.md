<div align="center" markdown>
<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/118521851/281424859-d9f20935-b6b1-4653-b676-0e590cf1ee91.png"/>

# Convert and copy multiple V7 datasets into Supervisely at once

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/v7-to-sly/migration_tool)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/v7-to-sly)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/v7-to-sly/migration_tool.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/v7-to-sly/migration_tool.png)](https://supervise.ly)

</div>

## Overview

This application allows you to copy multiple datasets from V7 instance to Supervisely instance, you can select which projects should be copied, labels and tags will be converted automatically. You can preview the results in the table, which will show URLs to corresdponding projects in V7 and Supervisely.
Every V7 dataset will be converted in a separate Supervisely project.<br>

\*️⃣ If you want to upload data, which was already exported from V7 instance, you can use this [Import V7](https://ecosystem.supervisely.com/apps/v7-to-sly/import_v7) app from Supervisely Ecosystem.<br>

## Preparation

In order to run the app, you need to obtain `API key` to work with V7 API. You can refer to [this documentation](https://docs.v7labs.com/reference/introduction#generating-an-api-key) to do it.

The API key should looks like this: `JUFxKUH.wfjargM-xZ3-K2wR2kkZaxFM-AqTiZWs`

Now you have two options to use your API key: you can use team files to store an .env file with or you can enter the API key directly in the app GUI. Using team files is recommended as it is more convenient and faster, but you can choose the option that is more suitable for you.

### Using team files

You can download an example of the .env file [here](https://github.com/supervisely-ecosystem/v7-to-supervisely/files/13297606/v7.env.zip) and edit it without any additional software in any text editor.<br>
NOTE: you need to unzip the file before using it.<br>

1. Create a .env file with the following content:
   `V7_API_KEY="JUFxKUH.wfjargM-xZ3-K2wR2kkZaxFM-AqTiZWs"`
2. Upload the .env file to the team files.
3. Right-click on the .env file, select `Run app` and choose the `V7 to Supervisely Migration Tool` app.

The app will be launched with the API key from the .env file and you won't need to enter it manually.
If everything was done correctly, you will see the following message in the app UI:

- ℹ️ Connection settings was loaded from .env file.
- ✅ Successfully connected to V7.

### Entering credentials manually

1. Launch the app from the Ecosystem.
2. Enter the V7 api key.
3. Press the `Connect to V7` button.

![credentials](https://github-production-user-asset-6210df.s3.amazonaws.com/118521851/281439246-4136d162-b274-4fa3-9c3f-518835ae5b21.png)

If everything was done correctly, you will see the following message in the app UI:

- ✅ Successfully connected to V7.<br>

NOTE: The app will not save your API key, you will need to enter it every time you launch the app. To save your time you can use the team files to store your credentials.

## How To Run

NOTE: In this section, we consider that you have already connected to V7 instance and have the necessary permissions to work with it. If you haven't done it yet, please refer to the [Preparation](#Preparation) section.<br>
So, here is the step-by-step guide on how to use the app:

**Step 1:** Select datasets to copy<br>
After connecting to the V7 instance, list of the datasets will be loaded into the widget automatically. You can select which datasets you want to copy to Supervisely and then press the `Select datasets` button.<br>

![select_datasets](https://github-production-user-asset-6210df.s3.amazonaws.com/118521851/281439252-71ee756d-8f28-4e9a-b8d8-952cb541f9ad.png)

**Step 2:** Take a look on list of projects<br>
After completing the `Step 1️⃣`, the application will retrieve information about the datasets from V7 API and show it in the table. Here you can find the links to the datasets in V7, and after copying the projects to Supervisely, links to the projects in Supervisely will be added to the table too.<br>

![datasets_table](https://github-production-user-asset-6210df.s3.amazonaws.com/118521851/281439254-9d5fd1cc-06d6-440a-a6ad-1e3cf4517a4a.png)<br>

**Step 3:** Press the `Copy` button<br>
Now you only need to press the `Copy` button and wait until the copying process is finished. You will see the statuses of the copying process for each dataset in the table. If any errors occur during the copying process, you will see the error status in the table. When the porcess is finished, you will see the total number of successfully copied projects and the total number of projects that failed to copy.<br>

ℹ️ V7 datasets can contain both images and videos, but Supervisely project can contain only one type of data. If the V7 dataset contains both images and videos, the application will create two projects in Supervisely: one with images and one with videos and you will find two links to the Supervisely projects in the table.<br>

ℹ️ Currently conversion of Cuboid geometry is not supported, corresponding annotations will be skipped.<br>
ℹ️ Supervisely doesn't support Ellipse geometry, this kind of labels will be skipped.<br>

![copy_projects](https://github-production-user-asset-6210df.s3.amazonaws.com/118521851/281439268-3aa73e14-54a7-403e-9e61-1a204fdea890.png)<br>

![finished](https://github-production-user-asset-6210df.s3.amazonaws.com/118521851/281439260-929148ce-9dbd-4249-b691-229a67b94ae1.png)<br>

The application will be stopped automatically after the copying process is finished.<br>

## Acknowledgement

- [darwin-py github](https://github.com/v7labs/darwin-py) ![GitHub Org's stars](https://img.shields.io/github/stars/v7labs/darwin-py?style=social)
- [V7 documentation](https://docs.v7labs.com/)
