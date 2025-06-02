from PyQt5.QtWidgets import QMessageBox


class TodoDeleter:
    """Static class for handling task deletion operations"""

    @staticmethod
    def delete_task(task_widget, save_callback):
        """Delete a task after confirmation"""
        reply = QMessageBox.question(
            task_widget.parent(),
            "Delete Task",
            "Are you sure you want to delete this task?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # Remove the widget from its parent layout
            parent_layout = task_widget.parent().layout()
            parent_layout.removeWidget(task_widget)
            task_widget.deleteLater()
            save_callback()

    @staticmethod
    def clear_all_tasks(task_container, save_callback):
        """Clear all tasks after confirmation"""
        if not task_container:
            return

        reply = QMessageBox.question(
            task_container,
            "Clear All Tasks",
            "Are you sure you want to clear all tasks?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Clear all task widgets from the layout
            layout = task_container.layout()
            if layout:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                save_callback()
