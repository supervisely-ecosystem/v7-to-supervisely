import supervisely as sly

from supervisely.app.widgets import Container

import migration_tool.src.ui.keys as keys
import migration_tool.src.ui.selection as selection
import migration_tool.src.ui.copying as copying

layout = Container(widgets=[keys.card, selection.card, copying.card])

app = sly.Application(layout=layout)
