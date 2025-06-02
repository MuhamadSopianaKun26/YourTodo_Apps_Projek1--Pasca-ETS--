from PyQt5.QtWidgets import (
    QTableWidgetItem,
    QProgressDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer, QDate, QTime


class LoadingManager:
    """Manages loading animation and progress display"""

    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.loading_label = parent_widget.loadingLabel
        self.loading_movie = parent_widget.loadingMovie
        self.table = parent_widget.taskTable

    def start_loading(self):
        """Show loading animation and hide table"""
        self.loading_label.show()
        self.loading_movie.start()
        self.table.hide()

    def stop_loading(self):
        """Hide loading animation and show table"""
        self.loading_label.hide()
        self.loading_movie.stop()
        self.table.show()


class TodoReader:
    """Static class for handling task reading operations"""

    @staticmethod
    def load_tasks_to_table(table_widget, file_path, show_loading=True):
        """Load tasks from file to table with optional loading animation"""
        if show_loading:
            # Create loading manager
            loading_manager = LoadingManager(table_widget.parent())
            loading_manager.start_loading()

            # Create and show progress dialog
            progress = QProgressDialog(
                "Loading tasks...", None, 0, 100, table_widget.parent()
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.setAutoClose(True)
            progress.setValue(0)

            # Timer to simulate loading and update progress
            timer = QTimer(table_widget.parent())
            progress_value = 0

            def update_progress():
                nonlocal progress_value
                progress_value += 20
                progress.setValue(progress_value)

                if progress_value >= 100:
                    timer.stop()
                    TodoReader._load_tasks_data(table_widget, file_path)
                    progress.close()
                    loading_manager.stop_loading()

            timer.timeout.connect(update_progress)
            timer.start(200)  # Update every 200ms
        else:
            TodoReader._load_tasks_data(table_widget, file_path)

    @staticmethod
    def _load_tasks_data(table_widget, file_path):
        """Load task data from file into table widget"""
        try:
            table_widget.setRowCount(0)  # Clear existing rows first
            with open(file_path, "r", encoding="utf-8") as file:
                tasks = file.readlines()  # Read all tasks first

                for line in tasks:
                    data = line.strip().split(" | ")
                    if len(data) == 6:  # Changed to 6 for start_time
                        row = table_widget.rowCount()
                        table_widget.insertRow(row)
                        for col, value in enumerate(data):
                            item = QTableWidgetItem(value)
                            table_widget.setItem(row, col, item)

        except FileNotFoundError:
            open(file_path, "w").close()
        except Exception as e:
            QMessageBox.critical(
                table_widget.parent(), "Error", f"Error loading tasks: {e}"
            )

    @staticmethod
    def get_selected_task_data(table_widget):
        """Get data of the currently selected task"""
        selected = table_widget.currentRow()
        if selected >= 0:
            return {
                "name": table_widget.item(selected, 0).text(),
                "description": table_widget.item(selected, 1).text(),
                "start_time": table_widget.item(selected, 2).text(),
                "deadline": table_widget.item(selected, 3).text(),
                "priority": table_widget.item(selected, 4).text(),
                "status": table_widget.item(selected, 5).text(),
            }
        return None

    @staticmethod
    def check_past_deadline_tasks(table_widget, mark_failed_callback):
        """Check and mark tasks that are past their deadline"""
        for row in range(table_widget.rowCount()):
            deadline_str = table_widget.item(
                row, 3
            ).text()  # Updated index for deadline
            deadline_date = QDate.fromString(deadline_str.split()[0], "yyyy-MM-dd")
            deadline_time = QTime.fromString(deadline_str.split()[1], "HH:mm")
            current_date = QDate.currentDate()
            current_time = QTime.currentTime()

            if (deadline_date < current_date) or (
                deadline_date == current_date and deadline_time < current_time
            ):
                if (
                    table_widget.item(row, 5).text() == "due"
                ):  # Updated index for status
                    mark_failed_callback(row)
