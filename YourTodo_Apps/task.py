from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QMessageBox,
    QStackedWidget,
)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QIcon

from main_components import TaskItemWidget, LoadingWidget
from path_utils import get_image_path, get_database_path

class TaskManager:
    def __init__(self, main_app):
        self.main_app = main_app
        self.task_list_layout = None
        self.content_stack = None
        self.loading_widget = None
        self.task_count_label = None
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
        if self.task_list_layout:
            while self.task_list_layout.count():
                item = self.task_list_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        try:
            if not self.main_app.current_user:
                return

            tasks_data = []
            task_file = get_database_path("tasks.txt")
            schedule_file = get_database_path("scheduled_tasks.txt")
            # Load tasks from tasks.txt
            try:
                with open(task_file, "r", encoding="utf-8") as file:
                    for line in file:
                        data = line.strip().split(" | ")
                        if len(data) >= 9 and data[-1] == self.main_app.current_user:
                            task_dict = {
                                "name": data[0],
                                "description": data[1],
                                "start_time": data[2],
                                "deadline": data[3],
                                "priority": data[4],
                                "reminder": data[5],
                                "status": data[6],
                                "schedule": data[7],
                                "username": data[8]
                            }
                            tasks_data.append(task_dict)
            except FileNotFoundError:
                open(task_file, "w", encoding="utf-8").close()

            # Load tasks from scheduled_tasks.txt
            try:
                with open(schedule_file, "r", encoding="utf-8") as file:
                    for line in file:
                        if line.startswith('#'):  # Skip comments
                            continue
                        data = line.strip().split(" | ")
                        if len(data) >= 9 and data[-1] == self.main_app.current_user:
                            task_dict = {
                                "name": data[0],
                                "description": data[1],
                                "start_time": data[2],
                                "deadline": data[3],
                                "priority": data[4],
                                "reminder": data[5],
                                "status": data[6],
                                "schedule": data[7],
                                "username": data[8]
                            }
                            # Only add if not already in tasks_data (avoid duplicates)
                            if not any(t["name"] == task_dict["name"] and 
                                     t["description"] == task_dict["description"] and
                                     t["start_time"] == task_dict["start_time"] and
                                     t["deadline"] == task_dict["deadline"] for t in tasks_data):
                                tasks_data.append(task_dict)
            except FileNotFoundError:
                pass

            for task_data in tasks_data:
                task_widget = TaskItemWidget(task_data, self.main_app)
                self.task_list_layout.addWidget(task_widget)

        except Exception as e:
            QMessageBox.critical(self.main_app, "Error", f"Error loading tasks: {e}")

        self.updateTaskCount()

    def addTask(self):
        """Open dialog to create a new task."""
        from create import TodoCreator
        TodoCreator.add_task(self.main_app, self.saveNewTask)

    def saveNewTask(self, task_data):
        """Save new task and update UI."""

        schedule_file = get_database_path("scheduled_tasks.txt")
        try:
            task_widget = TaskItemWidget(task_data, self.main_app)
            self.task_list_layout.addWidget(task_widget)
            
            # Save task to tasks.txt
            self.saveTasks()
            
            # If task has a schedule, save it to scheduled_tasks.txt
            schedule = task_data.get("schedule", "None")
            if schedule and schedule.lower() != "none":
                try:
                    # Read existing scheduled tasks
                    scheduled_tasks = []
                    try:
                        with open(schedule_file, "r", encoding="utf-8") as file:
                            for line in file:
                                if not line.startswith('#'):  # Skip comments
                                    scheduled_tasks.append(line.strip())
                    except FileNotFoundError:
                        # Create file with headers if it doesn't exist
                        with open(schedule_file, "w", encoding="utf-8") as file:
                            file.write("# File ini menyimpan task yang memiliki jadwal (daily, weekly, monthly)\n")
                            file.write("# Format: name | description | start_time | deadline | priority | reminder | status | schedule | username\n")
                    
                    # Create task string
                    task_str = f"{task_data['name']} | {task_data['description']} | {task_data['start_time']} | {task_data['deadline']} | {task_data['priority']} | {task_data.get('reminder', 'None')} | {task_data['status']} | {schedule} | {self.main_app.current_user}"
                    
                    # Add new task
                    scheduled_tasks.append(task_str)
                    
                    # Write back to file
                    with open(schedule_file, "w", encoding="utf-8") as file:
                        file.write("# File ini menyimpan task yang memiliki jadwal (daily, weekly, monthly)\n")
                        file.write("# Format: name | description | start_time | deadline | priority | reminder | status | schedule | username\n\n")
                        for task in scheduled_tasks:
                            file.write(task)
                            
                    print(f"Saved scheduled task to scheduled_tasks.txt: {task_data['name']}")
                except Exception as e:
                    print(f"Error saving to scheduled_tasks.txt: {e}")
            
            self.updateTaskCount()
        except Exception as e:
            print(f"Error saving task: {e}")
            # Don't show error message to prevent crashes
            # QMessageBox.critical(self.main_app, "Error", f"Error saving task: {e}")

    def saveTasks(self):
        """Save all tasks to file, preserving tasks from other users."""
        tasks_file = get_database_path("tasks.txt")

        try:
            if not self.main_app or not hasattr(self.main_app, 'current_user') or not self.main_app.current_user:
                print("Cannot save tasks: No current user")
                return

            # First, read all existing tasks
            all_tasks = []
            try:
                with open(tasks_file, "r", encoding="utf-8") as file:
                    for line in file:
                        data = line.strip().split(" | ")
                        if len(data) >= 7 and data[-1] != self.main_app.current_user:
                            all_tasks.append(line.strip())
            except FileNotFoundError:
                pass

            # Add current user's tasks
            if self.task_list_layout:
                for i in range(self.task_list_layout.count()):
                    widget = self.task_list_layout.itemAt(i).widget()
                    if isinstance(widget, TaskItemWidget):
                        task_data = widget.task_data
                        task_data["username"] = self.main_app.current_user
                        
                        # Ensure schedule is "None" if it's "Add as Schedule"
                        schedule = task_data.get("schedule", "None")
                        if schedule == "Add as Schedule":
                            schedule = "None"
                            
                        data = [
                            task_data["name"],
                            task_data["description"],
                            task_data["start_time"],
                            task_data["deadline"],
                            task_data["priority"],
                            task_data.get("reminder", "None"),
                            task_data["status"],
                            schedule,
                            task_data["username"]
                        ]
                        all_tasks.append(" | ".join(data))

            # Write all tasks back to file
            with open(tasks_file, "w", encoding="utf-8") as file:
                for task in all_tasks:
                    file.write(task+"\n")

            self.updateTaskCount()
        except Exception as e:
            print(f"Error saving tasks: {e}")
            # Don't show error message to prevent crashes
            # QMessageBox.critical(self.main_app, "Error", f"Error saving tasks: {e}")

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