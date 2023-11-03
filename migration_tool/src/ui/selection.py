from typing import NamedTuple
import supervisely as sly
from supervisely.app.widgets import Card, Transfer, Button, Container

import migration_tool.src.globals as g
import migration_tool.src.ui.copying as copying
from migration_tool.src.v7_api import get_datasets

datasets_transfer = Transfer(
    filterable=True,
    filter_placeholder="Input dataset name",
    titles=["Available datasets", "Datasets to copy"],
)

select_datasets_button = Button("Select datasets")
select_datasets_button.disable()
change_selection_button = Button("Change datasets")
change_selection_button.hide()

card = Card(
    title="2️⃣ Selection",
    description="Select datasets to copy from V7 to Supervisely.",
    content=Container([datasets_transfer, select_datasets_button]),
    content_top_right=change_selection_button,
    collapsable=True,
)
card.lock()
card.collapse()


def fill_transfer_with_datasets() -> None:
    """Fills the transfer widget with datasets sorted by id from V7 API.
    On every launch clears the items in the widget and fills it with new datasets."""

    sly.logger.debug("Starting to build transfer widget with datasets.")
    transfer_items = []

    for dataset in get_datasets():
        g.STATE.datasets[dataset.dataset_id] = dataset
        transfer_items.append(
            Transfer.Item(
                key=dataset.dataset_id, label=f"[{dataset.dataset_id}] {dataset.name}"
            )
        )

    sly.logger.debug(f"Prepared {len(transfer_items)} items for transfer.")

    transfer_items.sort(key=lambda item: item.key)
    datasets_transfer.set_items(transfer_items)
    sly.logger.debug("Transfer widget filled with datasets.")


@datasets_transfer.value_changed
def project_changed(items: NamedTuple) -> None:
    """Enables or disables the select datasets button depending on the selected
    datasets in the transfer widget. If at least one dataset is selected, the button is enabled.
    Otherwise, the button is disabled.

    :param items: namedtuple containing two lists (transferred_items and untransferred_items)
    :type items: NamedTuple
    """
    if items.transferred_items:
        select_datasets_button.enable()
    else:
        select_datasets_button.disable()


@select_datasets_button.click
def select_datasets() -> None:
    """Saves the selected datasets to the global state and builds the datasets table."""

    dataset_ids = datasets_transfer.get_transferred_items()

    sly.logger.debug(
        f"Select datasets button clicked, selected dataset IDs: {dataset_ids}. Will save them to the global state."
    )
    g.STATE.selected_datasets = dataset_ids

    copying.build_datasets_table()

    card.lock()
    card.collapse()
    copying.card.unlock()
    copying.card.uncollapse()

    change_selection_button.show()


@change_selection_button.click
def change_selection() -> None:
    """Changes the widget states and resets the selected projects in the global state."""

    sly.logger.debug(
        "Change selection button clicked, will change widget states "
        "And reset selected projects in the global state."
    )

    g.STATE.datasets = dict()
    g.STATE.selected_projects = None

    card.unlock()
    card.uncollapse()

    copying.card.lock()
    copying.card.collapse()

    change_selection_button.hide()
