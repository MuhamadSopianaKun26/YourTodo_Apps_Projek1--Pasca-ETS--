from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QDate
from _darrel.create import TaskDialog
from _sopian.path_utils import get_database_path
import json


class TodoUpdater:
    """
    Static class providing task update operations.
    Handles task editing, status changes, and moving tasks to history.
    """

    @staticmethod
    def update_task(task_widget, save_callback):
        """
        Open dialog to edit task properties.

        Args:
            task_widget: The widget containing task data to be updated
            save_callback: Function to call after successful update
        """
        # Store current username before update
        current_username = task_widget.task_data.get("username")
        
        dialog = TaskDialog(task_widget.main_window, task_widget.task_data)
        if dialog.exec_():
            updated_data = dialog.get_task_data()
            if updated_data:
                # Ensure username is preserved
                updated_data["username"] = current_username
                task_widget.task_data = updated_data
                save_callback()

    @staticmethod
    def mark_task_as_done(task_widget, save_callback):
        """
        Mark task as completed with current date.

        Args:
            task_widget: The widget containing task data to be marked as done
            save_callback: Function to call after status update
        """
        current_date = QDate.currentDate().toString("yyyy-MM-dd")
        task_widget.task_data["status"] = f"done - Completed on {current_date}"
        save_callback()

    @staticmethod
    def mark_task_as_failed(task_widget, save_callback):
        """
        Mark task as failed.

        Args:
            task_widget: The widget containing task data to be marked as failed
            save_callback: Function to call after status update
        """
        current_date = QDate.currentDate().toString("yyyy-MM-dd")
        task_widget.task_data["status"] = f"failed - Completed on {current_date}"
        save_callback()

    @staticmethod
    def move_task_to_history(task_widget, save_callback):
        """
        Move completed or failed task to history file.
        Task must not be in 'due' status to be moved.

        Args:
            task_widget: The widget containing task data to be moved
            save_callback: Function to call after successful move
        """
        if task_widget.task_data["status"] == "due":
            QMessageBox.warning(
                task_widget.main_window,
                "Cannot Move Task",
                "Task cannot be moved to history while its status is still 'due'",
            )
            return

        history_file = get_database_path("history.json")
        try:
            # Read existing history
            try:
                with open(history_file, "r", encoding="utf-8") as file:
                    history_data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                history_data = {"history": []}

            # Add new task to history
            history_data["history"].append(task_widget.task_data)

            # Write updated history back to file
            with open(history_file, "w", encoding="utf-8") as file:
                json.dump(history_data, file, indent=2)

            # Remove task widget from UI
            parent_layout = task_widget.parent().layout()
            parent_layout.removeWidget(task_widget)
            task_widget.deleteLater()

            save_callback()
            QMessageBox.information(
                task_widget.main_window,
                "Success",
                "Task has been moved to history successfully!",
            )
        except Exception as e:
            QMessageBox.critical(
                task_widget.main_window,
                "Error",
                f"Error moving task to history: {e}",
            )
