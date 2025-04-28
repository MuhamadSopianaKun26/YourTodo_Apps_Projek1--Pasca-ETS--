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
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from ui_components import TaskItemWidget, LoadingWidget
from path_utils import get_image_path
from filter import TaskFilter

class TaskManager:
    def __init__(self, main_app):
        self.main_app = main_app
        self.task_list_layout = None
        self.content_stack = None
        self.loading_widget = None
        self.task_count_label = None
        self.filter_combo = None
        self.task_filter = TaskFilter()
        
        # Button styles
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

        # Header with task count
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

        # Action buttons row (now only filter controls on the left)
        action_btn_layout = QHBoxLayout()
        
        # Filter container (combo box + button)
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
        
        # Filter button    
        action_btn_layout.addWidget(filter_container)
        action_btn_layout.addStretch()

        # Add other action buttons
        add_btn = self._createActionButton("Add Task", get_image_path("add.png"))
        add_btn.clicked.connect(self.addTask)
        action_btn_layout.addWidget(add_btn)

        clear_btn = self._createActionButton("Clear All", get_image_path("clear.png"))
        clear_btn.clicked.connect(self.clearAllTasks)
        action_btn_layout.addWidget(clear_btn)

        refresh_btn = self._createActionButton("Refresh", get_image_path("refresh.png"))
        refresh_btn.clicked.connect(self.refreshTasks)
        action_btn_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)
        layout.addLayout(action_btn_layout)

        # Task list area
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

    def applyFilters(self):
        """Apply filters using the TaskFilter class"""
        filter_text = self.filter_combo.currentText()
        self.task_filter.filter_tasks(self.task_list_layout, filter_text)

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
            
            # Load tasks from tasks.txt
            try:
                with open("tasks.txt", "r", encoding="utf-8") as file:
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
                open("tasks.txt", "w", encoding="utf-8").close()

            # Load tasks from scheduled_tasks.txt
            try:
                with open("scheduled_tasks.txt", "r", encoding="utf-8") as file:
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
                        with open("scheduled_tasks.txt", "r", encoding="utf-8") as file:
                            for line in file:
                                if not line.startswith('#'):  # Skip comments
                                    scheduled_tasks.append(line.strip())
                    except FileNotFoundError:
                        # Create file with headers if it doesn't exist
                        with open("scheduled_tasks.txt", "w", encoding="utf-8") as file:
                            file.write("# File ini menyimpan task yang memiliki jadwal (daily, weekly, monthly)\n")
                            file.write("# Format: name | description | start_time | deadline | priority | reminder | status | schedule | username\n")
                    
                    # Create task string
                    task_str = f"{task_data['name']} | {task_data['description']} | {task_data['start_time']} | {task_data['deadline']} | {task_data['priority']} | {task_data.get('reminder', 'None')} | {task_data['status']} | {schedule} | {self.main_app.current_user}"
                    
                    # Add new task
                    scheduled_tasks.append(task_str)
                    
                    # Write back to file
                    with open("scheduled_tasks.txt", "w", encoding="utf-8") as file:
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

    def saveTasks(self):
        """Save all tasks to file, preserving tasks from other users."""
        try:
            if not self.main_app or not hasattr(self.main_app, 'current_user') or not self.main_app.current_user:
                print("Cannot save tasks: No current user")
                return

            # First, read all existing tasks
            all_tasks = []
            try:
                with open("tasks.txt", "r", encoding="utf-8") as file:
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
            with open("tasks.txt", "w", encoding="utf-8") as file:
                for task in all_tasks:
                    file.write(task+"\n")

            self.updateTaskCount()
        except Exception as e:
            print(f"Error saving tasks: {e}")

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
        self.loadTasks()
        self.saveTasks()
        self.content_stack.setCurrentWidget(self.content_stack.widget(0))