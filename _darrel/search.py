from PyQt5.QtWidgets import QLabel, QListWidget, QListWidgetItem, QLayout


def find_all_labels(layout):
    """
    Recursively find all QLabel widgets in a layout.
    Args:
        layout (QLayout): The layout to search.
    Returns:
        list of QLabel: All QLabel widgets found in the layout.
    """
    labels = []
    for i in range(layout.count()):
        item = layout.itemAt(i)
        widget = item.widget()
        if widget and isinstance(widget, QLabel):
            labels.append(widget)
        elif item.layout():
            labels.extend(find_all_labels(item.layout()))
    return labels


def filter_list_widget_by_query(list_widget, query):
    """
    Show/hide QListWidget items based on search query (matches name or description, case-insensitive).
    Args:
        list_widget (QListWidget): The list widget to filter.
        query (str): The search query.
    """
    query = query.strip().lower()
    for i in range(list_widget.count()):
        item = list_widget.item(i)
        widget = list_widget.itemWidget(item)
        labels = find_all_labels(widget.layout()) if widget else []
        name = labels[0].text().lower() if len(labels) > 0 else ""
        desc = labels[1].text().lower() if len(labels) > 1 else ""
        if not query or query in name or query in desc:
            item.setHidden(False)
        else:
            item.setHidden(True)


def filter_layout_widgets_by_query(layout, query):
    """
    Show/hide widgets in a QVBoxLayout based on search query (matches name or description, case-insensitive).
    Args:
        layout (QLayout): The layout containing widgets to filter.
        query (str): The search query.
    """
    query = query.strip().lower()
    for i in range(layout.count()):
        widget = layout.itemAt(i).widget()
        if not widget:
            continue
        labels = find_all_labels(widget.layout()) if widget.layout() else []
        name = labels[0].text().lower() if len(labels) > 0 else ""
        desc = labels[1].text().lower() if len(labels) > 1 else ""
        if not query or query in name or query in desc:
            widget.show()
        else:
            widget.hide()
