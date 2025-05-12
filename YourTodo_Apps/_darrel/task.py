from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QMessageBox,
    QStackedWidget,
    QComboBox,
)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QIcon
import json

from _sopian.main_components import TaskItemWidget, LoadingWidget
from _sopian.path_utils import get_image_path, get_database_path
from _rizqi.filter import TaskFilter


class TaskManager:
    def __init__(self, main_app):
        self.main_app = main_app
        self.task_list_layout = None
        self.content_stack = None
        self.loading_widget = None
        self.task_count_label = None
        self.filter_combo = None
        self.task_filter = TaskFilter()
        self.action_button_style = """
            QPushButton {
                background-color: #00B4D8;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0096B7;
            }
        """
        self.filter_button_style = """
            QPushButton {
                background-color: #00B4D8;
                border: none;
                border-radius: 15px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #0096B7;
            }
        """

    def setupTasksWidget(self):
        """Set up the Tasks section widget with task list and action buttons."""
        self.tasks_widget = QWidget()
        layout = QVBoxLayout(self.tasks_widget)

        header_layout = QHBoxLayout()
        self.task_count_label = QLabel("Tasks: 0")
        self.task_count_label.setStyleSheet(
            """
            QLabel {
                color: #333;
                font-size: 24px;
                font-weight: bold;
            }
        """
        )
        header_layout.addWidget(self.task_count_label)
        header_layout.addStretch()

        # Filter container (combo box)
        filter_container = QWidget()
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(5)

        # Filter combo box
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Tasks")
        self.filter_combo.addItem("High Priority")
        self.filter_combo.addItem("Medium Priority")
        self.filter_combo.addItem("Low Priority")
        self.filter_combo.addItem("Completed")
        self.filter_combo.addItem("Pending")
        self.filter_combo.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 15px;
                min-width: 150px;
            }
        """
        )
        self.filter_combo.currentIndexChanged.connect(self.applyFilters)
        filter_layout.addWidget(self.filter_combo)

        header_layout.addWidget(filter_container)
        header_layout.addStretch()

        add_btn = self._createActionButton("Add Task", get_image_path("add.png"))
        add_btn.clicked.connect(self.addTask)
        header_layout.addWidget(add_btn)

        clear_btn = self._createActionButton("Clear All", get_image_path("clear.png"))
        clear_btn.clicked.connect(self.clearAllTasks)
        header_layout.addWidget(clear_btn)

        refresh_btn = self._createActionButton("Refresh", get_image_path("refresh.png"))
        refresh_btn.clicked.connect(self.refreshTasks)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)

        scroll = self._setupTaskList()
        self.loading_widget = LoadingWidget()

        self.content_stack.addWidget(scroll)
        self.content_stack.addWidget(self.loading_widget)
        self.content_stack.setCurrentWidget(scroll)

        return self.tasks_widget

    def applyFilters(self):
        """Apply filters using the TaskFilter class"""
        filter_text = self.filter_combo.currentText()
        self.task_filter.filter_tasks(self.task_list_layout, filter_text)

    def _createActionButton(self, text, icon_path=None):
        """Create a styled action button with optional icon."""
        btn = QPushButton(text)
        if icon_path:
            btn.setIcon(QIcon(icon_path))
        btn.setStyleSheet(self.action_button_style)
        return btn

    def clearAllTasks(self):
        """Clear all tasks after user confirmation."""
        reply = QMessageBox.question(
            self.main_app,
            "Clear All Tasks",
            "Are you sure you want to clear all tasks?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.task_list_layout:
                while self.task_list_layout.count():
                    item = self.task_list_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

                self.saveTasks()
                self.updateTaskCount()

    def _setupTaskList(self):
        """Create and return a scrollable task list area."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background-color: transparent; }"
        )

        self.task_list_widget = QWidget()
        self.task_list_layout = QVBoxLayout(self.task_list_widget)
        self.task_list_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.task_list_widget)

        return scroll

    def loadTasks(self):
        """Load tasks from file for the current user and update UI."""
        try:
            if not self.main_app.current_user:
                return

            tasks_data = []
            task_file = get_database_path("tasks.json")

            # Load tasks from tasks.json
            try:
                with open(task_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    for task in data.get("tasks", []):
                        if task["username"] == self.main_app.current_user:
                            tasks_data.append(task)
            except FileNotFoundError:
                with open(task_file, "w", encoding="utf-8") as file:
                    json.dump({"tasks": []}, file, indent=2)
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Invalid JSON format in tasks file")
                return

            # Clear existing tasks from UI
            for i in reversed(range(self.task_list_layout.count())):
                self.task_list_layout.itemAt(i).widget().setParent(None)

            # Add tasks to UI
            for task_data in tasks_data:
                task_widget = TaskItemWidget(task_data, self.main_app)
                self.task_list_layout.addWidget(task_widget)

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error loading tasks: {str(e)}")

        self.updateTaskCount()

    def addTask(self):
        """Open dialog to create a new task."""
        from create import TodoCreator

        TodoCreator.add_task(self.main_app, self.saveNewTask)

    def saveNewTask(self, task_data):
        """Save new task and update UI."""
        try:
            task_widget = TaskItemWidget(task_data, self.main_app)
            self.task_list_layout.addWidget(task_widget)

            # Save task to tasks.json
            self.saveTasks()

            # If task has a schedule, save it to scheduled_tasks.json
            schedule = task_data.get("schedule", "None")
            if schedule and schedule.lower() != "none":
                schedule_file = get_database_path("scheduled_tasks.json")
                try:
                    # Read existing scheduled tasks
                    try:
                        with open(schedule_file, "r", encoding="utf-8") as file:
                            data = json.load(file)
                            scheduled_tasks = data.get("scheduled_tasks", [])
                    except (FileNotFoundError, json.JSONDecodeError):
                        scheduled_tasks = []

                    # Add new scheduled task
                    task_data["is_active"] = True
                    task_data["last_run_date"] = task_data["start_time"].split()[0]
                    scheduled_tasks.append(task_data)

                    # Save updated scheduled tasks
                    with open(schedule_file, "w", encoding="utf-8") as file:
                        json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

                except Exception as e:
                    QMessageBox.critical(
                        None, "Error", f"Error saving scheduled task: {str(e)}"
                    )

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error adding task: {str(e)}")

    def saveTasks(self):
        """Save all tasks to file."""
        try:
            tasks_data = []
            task_file = get_database_path("tasks.json")

            # Get existing tasks for other users
            try:
                with open(task_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    tasks_data = [
                        task
                        for task in data.get("tasks", [])
                        if task["username"] != self.main_app.current_user
                    ]
            except FileNotFoundError:
                pass
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Invalid JSON format in tasks file")
                return

            # Add current user's tasks
            for i in range(self.task_list_layout.count()):
                widget = self.task_list_layout.itemAt(i).widget()
                if isinstance(widget, TaskItemWidget):
                    tasks_data.append(widget.task_data)

            # Save all tasks
            with open(task_file, "w", encoding="utf-8") as file:
                json.dump({"tasks": tasks_data}, file, indent=2)

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error saving tasks: {str(e)}")

    def updateTaskCount(self):
        """Update the task count display."""
        count = self.task_list_layout.count() if self.task_list_layout else 0
        self.task_count_label.setText(f"Tasks: {count}")

    def refreshTasks(self):
        """Refresh tasks with loading animation."""
        self.content_stack.setCurrentWidget(self.loading_widget)
        QTimer.singleShot(1000, self._performRefresh)

    def _performRefresh(self):
        """Perform the actual refresh operation."""
        # Load tasks first to ensure we have all tasks
        self.loadTasks()
        # Then save to preserve any changes
        self.saveTasks()
        self.content_stack.setCurrentWidget(self.content_stack.widget(0))

    def deleteTask(self, task_widget):
        """Delete a task."""
        try:
            # Remove from UI
            task_widget.setParent(None)

            # Save changes to file
            self.saveTasks()

            # If it's a scheduled task, remove from scheduled_tasks.json
            if task_widget.task_data.get("schedule", "None").lower() != "none":
                schedule_file = get_database_path("scheduled_tasks.json")
                try:
                    with open(schedule_file, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        scheduled_tasks = data.get("scheduled_tasks", [])

                    # Remove matching task
                    scheduled_tasks = [
                        task
                        for task in scheduled_tasks
                        if not (
                            task["name"] == task_widget.task_data["name"]
                            and task["username"] == task_widget.task_data["username"]
                        )
                    ]

                    with open(schedule_file, "w", encoding="utf-8") as file:
                        json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

                except Exception as e:
                    QMessageBox.critical(
                        None, "Error", f"Error removing scheduled task: {str(e)}"
                    )

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error deleting task: {str(e)}")

    def moveToHistory(self, task_widget):
        """Move a completed or failed task to history."""
        try:
            history_file = get_database_path("history.json")

            # Load existing history
            try:
                with open(history_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    history = data.get("history", [])
            except (FileNotFoundError, json.JSONDecodeError):
                history = []

            # Add task to history
            history.append(task_widget.task_data)

            # Save updated history
            with open(history_file, "w", encoding="utf-8") as file:
                json.dump({"history": history}, file, indent=2)

            # Delete task from active tasks
            self.deleteTask(task_widget)

        except Exception as e:
            QMessageBox.critical(
                None, "Error", f"Error moving task to history: {str(e)}"
            )
