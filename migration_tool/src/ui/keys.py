import supervisely as sly

from supervisely.app.widgets import Card, Text, Input, Field, Button, Container

import migration_tool.src.globals as g
import migration_tool.src.ui.selection as selection
from migration_tool.src.v7_api import get_configurtation


v7_api_key_input = Input(minlength=1, type="password", placeholder="for example: admin")
v7_api_key_field = Field(
    title="V7 API key",
    description="API key to access the V7 API.",
    content=v7_api_key_input,
)

connect_button = Button("Connect to V7")
connect_button.disable()
change_connection_button = Button("Change settings")
change_connection_button.hide()

load_from_env_text = Text(
    "Connection settings was loaded from .env file.", status="info"
)
load_from_env_text.hide()
connection_status_text = Text()
connection_status_text.hide()

card = Card(
    title="1️⃣ V7 connection",
    description="Enter your V7 API key and check the connection.",
    content=Container(
        [
            v7_api_key_field,
            connect_button,
            load_from_env_text,
            connection_status_text,
        ]
    ),
    content_top_right=change_connection_button,
    collapsable=True,
)


def connected() -> None:
    """Changes the state of the widgets if the app successfully connected to the V7 server.
    Launches the process of filling the transfer with projects from V7 API."""

    sly.logger.debug("Status changed to connected, will change widget states.")
    v7_api_key_input.disable()
    connect_button.disable()

    selection.card.unlock()
    selection.card.uncollapse()

    change_connection_button.show()
    connection_status_text.status = "success"
    connection_status_text.text = "Successfully connected to V7."

    connection_status_text.show()
    selection.fill_transfer_with_datasets()


def disconnected(with_error=False) -> None:
    """Changes the state of the widgets if the app disconnected from the V7 server.
    Depending on the value of the with_error parameter, the status text will be different.

    :param with_error: if the app was disconnected from server or by a pressing change button, defaults to False
    :type with_error: bool, optional
    """

    sly.logger.debug(
        f"Status changed to disconnected with error: {with_error}, will change widget states."
    )
    v7_api_key_input.enable()
    connect_button.enable()

    card.uncollapse()
    selection.card.lock()
    selection.card.collapse()

    change_connection_button.hide()

    if with_error:
        connection_status_text.status = "error"
        connection_status_text.text = "Failed to connect to V7."

    else:
        connection_status_text.status = "warning"
        connection_status_text.text = "Disconnected from V7."

    g.STATE.clear_v7_credentials()
    connection_status_text.show()


@v7_api_key_input.value_changed
def change_connect_button_state(_: str) -> None:
    """Enables the connect button if all the required fields are filled,
    otherwise disables it.

    :param _: Unused (value from the widget)
    :type input_value: str
    """
    if all(
        [
            v7_api_key_input.get_value(),
        ]
    ):
        connect_button.enable()

    else:
        connect_button.disable()


@connect_button.click
def try_to_connect() -> None:
    """Save the V7 credentials from the widgets to the global State and try to connect to the V7 server.
    Depending on the result of the connection, the state of the widgets will change."""
    g.STATE.v7_api_key = v7_api_key_input.get_value()

    sly.logger.debug("Saved V7 credentials in global State. ")

    connection_status = get_configurtation()

    if connection_status:
        connected()
    else:
        disconnected(with_error=True)


if g.STATE.loaded_from_env:
    sly.logger.debug('The application was started with the "Load from .env" option.')

    load_from_env_text.show()

    v7_api_key_input.set_value(g.STATE.v7_api_key)
    connect_button.enable()

    connection_status = get_configurtation()

    if connection_status:
        sly.logger.info("Connection to V7 server was successful.")

        connected()

    else:
        sly.logger.warning("Connection to V7 server failed.")

        disconnected(with_error=True)
