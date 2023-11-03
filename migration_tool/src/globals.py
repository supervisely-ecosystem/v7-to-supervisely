import os

from collections import namedtuple
import supervisely as sly

from dotenv import load_dotenv

ABSOLUTE_PATH = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(ABSOLUTE_PATH)
sly.logger.debug(f"Absolute path: {ABSOLUTE_PATH}, parent dir: {PARENT_DIR}")

if sly.is_development():
    # * For convinient development, has no effect in the production.
    local_env_path = os.path.join(PARENT_DIR, "local.env")
    supervisely_env_path = os.path.expanduser("~/supervisely.env")
    sly.logger.debug(
        "Running in development mode. Will load .env files... "
        f"Local .env path: {local_env_path}, Supervisely .env path: {supervisely_env_path}"
    )

    if os.path.exists(local_env_path) and os.path.exists(supervisely_env_path):
        sly.logger.debug("Both .env files exists. Will load them.")
        load_dotenv(local_env_path)
        load_dotenv(supervisely_env_path)
    else:
        sly.logger.warning("One of the .env files is missing. It may cause errors.")

api: sly.Api = sly.Api.from_env()

TEMP_DIR = os.path.join(PARENT_DIR, "temp")

# * Directory, where downloaded V7 datasets will be stored.
DOWNLOAD_DIR = os.path.join(TEMP_DIR, "downloads")

# * Directory, where prepared V7 datasets will be stored.
PREPARED_DIR = os.path.join(TEMP_DIR, "prepared")
sly.fs.mkdir(DOWNLOAD_DIR, remove_content_if_exists=True)
sly.fs.mkdir(PREPARED_DIR, remove_content_if_exists=True)
sly.logger.debug(f"Download dir: {DOWNLOAD_DIR}, prepared dir: {PREPARED_DIR}")


class State:
    def __init__(self):
        self.selected_team = sly.io.env.team_id()
        self.selected_workspace = sly.io.env.workspace_id()

        # Will be set to True, if the app will be launched from .env file in Supervisely.
        self.loaded_from_env = False

        # V7 credentials to access the API.
        self.v7_api_key = None

        self.datasets = {}

        # Will be set to False if the cancel button will be pressed.
        # Sets to True on every click on the "Copy" button.
        self.continue_copying = True

    def clear_v7_credentials(self):
        """Clears the V7 credentials and sets them to None."""

        sly.logger.debug("Clearing CVAT credentials...")
        self.v7_api_key = None

    def load_from_env(self):
        """Downloads the .env file from Supervisely and reads the V7 credentials from it."""

        api.file.download(STATE.selected_team, V7_ENV_TEAMFILES, V7_ENV_FILE)
        sly.logger.debug(
            ".env file downloaded successfully. Will read the credentials."
        )

        load_dotenv(V7_ENV_FILE)

        self.v7_api_key = os.getenv("V7_API_KEY")
        sly.logger.debug(
            "V7 credentials readed successfully. Will check the connection."
        )
        self.loaded_from_env = True


STATE = State()
sly.logger.debug(
    f"Selected team: {STATE.selected_team}, selected workspace: {STATE.selected_workspace}"
)

# * Local path to the .env file with credentials, after downloading it from Supervisely.
V7_ENV_FILE = os.path.join(PARENT_DIR, "v7.env")
sly.logger.debug(f"Path to the local v7.env file: {V7_ENV_FILE}")

# * Path to the .env file with credentials (on Team Files).
# While local development can be set in local.env file with: context.slyFile = "/.env/v7.env"
V7_ENV_TEAMFILES = sly.env.file(raise_not_found=False)
sly.logger.debug(f"Path to the TeamFiles from environment: {V7_ENV_TEAMFILES}")

CopyingStatus = namedtuple("CopyingStatus", ["copied", "error", "waiting", "working"])
COPYING_STATUS = CopyingStatus("✅ Copied", "❌ Error", "⏳ Waiting", "🔄 Working")

if V7_ENV_TEAMFILES:
    sly.logger.debug(".env file is provided, will try to download it.")
    STATE.load_from_env()
