from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QCalendarWidget,
    QPushButton,
    QFrame,
    QStackedWidget,
    QComboBox,
    QDialog,
    QLineEdit,
    QTextEdit,
    QTimeEdit,
    QMessageBox,
    QMenu,
    QAction,
)
from PyQt5.QtGui import QFont, QColor, QPalette, QBrush, QMovie, QIcon
from PyQt5.QtCore import Qt, QDate, QDateTime, QTimer, QTime, QSize
import os
from datetime import datetime, timedelta
import calendar
from _sopian.path_utils import get_image_path, get_database_path
import json


class ScheduleWidget(QWidget):
    """
    Widget that displays the task schedule in a calendar view.
    Allows viewing and managing scheduled tasks.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Pastikan parent adalah instance dari ToDoApp
        if parent and hasattr(parent, "current_user"):
            self.main_app = parent
        else:
            print("Warning: ScheduleWidget initialized without proper ToDoApp instance")
            self.main_app = None
        self.scheduled_tasks = []
        self.initUI()
        self.loadScheduledTasks()
        # Panggil highlightDatesWithTasks setelah inisialisasi
        self.highlightDatesWithTasks()

        # Set up timer untuk memeriksa dan menambahkan task terjadwal
        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self.checkAndAddScheduledTasks)
        self.schedule_timer.start(15000)  # Periksa setiap 15 detik

    def initUI(self):
        """Initialize the schedule widget UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header = QHBoxLayout()
        title = QLabel("Schedule")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #333;")
        header.addWidget(title)
        header.addStretch()

        # View selector dropdown
        self.view_selector = QComboBox()
        self.view_selector.addItems(["Schedule", "Repeated Tasks"])
        self.view_selector.setStyleSheet(
            """
            QComboBox {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 3px 10px;
                font-weight: bold;
                font-size: 16px;
            }
            QComboBox:hover {
                background-color: #e0e0e0;
            }
            QComboBox::drop-down {
                padding: 5px; 
                border-radius: 5px
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
                font-family: "Arial";
                font-size: 12px;
                text: "▼";
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #333;
                selection-background-color: #E3F8FF;
                selection-color: #333;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QComboBox QAbstractItemView::item {
                padding: 12px 15px;
                min-height: 40px;
                border-radius: 4px;
                margin: 2px;
                font-size: 16px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #E3F8FF;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #E3F8FF;
                color: #00B4D8;
            }
        """
        )

        # Remove the custom widget approach
        self.view_selector.setEditable(False)
        self.view_selector.setInsertPolicy(QComboBox.NoInsert)

        # Create a custom button with arrow
        dropdown_container = QWidget()
        dropdown_layout = QHBoxLayout(dropdown_container)
        dropdown_layout.setContentsMargins(0, 0, 0, 0)
        dropdown_layout.setSpacing(0)

        # Add the combo box to the layout
        dropdown_layout.addWidget(self.view_selector)

        # Create a label for the arrow
        self.arrow_label = QLabel("▼")
        self.arrow_label.setStyleSheet(
            """
            color: #333;
            font-size: 14px;
            font-weight: bold;
            padding-right: 5px;
        """
        )
        self.arrow_label.setFixedWidth(20)
        self.arrow_label.setAlignment(Qt.AlignCenter)

        # Add the arrow label to the layout
        dropdown_layout.addWidget(self.arrow_label)

        # Add the container to the header
        header.addWidget(dropdown_container)

        # Connect signals to change arrow direction
        self.view_selector.view().installEventFilter(self)
        self.view_selector.currentTextChanged.connect(self.switchView)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #00B4D8;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 3px 10px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #0096B7;
            }
        """
        )
        refresh_btn.clicked.connect(self.refreshSchedule)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Content stack for switching between views
        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)

        # Calendar widget
        calendar_widget = QWidget()
        calendar_layout = QVBoxLayout(calendar_widget)
        calendar_layout.setContentsMargins(0, 0, 0, 0)
        calendar_layout.setSpacing(5)

        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet(
            """
            QCalendarWidget {
                background-color: white;
                border-radius: 8px;
                padding: 5px;
                font-size: 16px;
            }
            QCalendarWidget QToolButton {
                color: #333;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 2px;
                font-size: 16px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #E3F8FF;
            }
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
            }
            QCalendarWidget QSpinBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 2px;
                font-size: 12px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                font-size: 12px;
            }
        """
        )
        # Set fixed size for calendar
        self.calendar.setFixedHeight(250)
        calendar_layout.addWidget(self.calendar)

        # Task list for selected date
        self.task_list = QListWidget()
        self.task_list.setStyleSheet(
            """
            QListWidget {
                background: white;
                border-radius: 8px;
                padding: 5px;
                margin-top: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """
        )
        self.task_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        calendar_layout.addWidget(self.task_list)

        # Add calendar widget to content stack
        self.content_stack.addWidget(calendar_widget)

        # Create repeated tasks widget
        repeated_widget = QWidget()
        repeated_layout = QVBoxLayout(repeated_widget)
        repeated_layout.setContentsMargins(0, 0, 0, 0)

        # Add "Add Repeated Task" button
        add_task_btn = QPushButton("Add Repeated Task")
        add_task_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #00B4D8;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 12px;
                margin-bottom: 10px;
            }
            QPushButton:hover {
                background-color: #0096B7;
            }
        """
        )
        add_task_btn.clicked.connect(self.show_add_repeated_task_dialog)
        repeated_layout.addWidget(add_task_btn)

        # Add Clear All button
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FF5252;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 12px;
                margin-bottom: 10px;
            }
            QPushButton:hover {
                background-color: #FF1744;
            }
        """
        )
        clear_all_btn.clicked.connect(self.clearAllScheduledTasks)
        repeated_layout.addWidget(clear_all_btn)

        self.repeated_tasks_list = QListWidget()
        self.repeated_tasks_list.setStyleSheet(
            """
            QListWidget {
                background: white;
                border-radius: 8px;
                padding: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """
        )
        repeated_layout.addWidget(self.repeated_tasks_list)

        # Add repeated tasks widget to content stack
        self.content_stack.addWidget(repeated_widget)

        # Create loading widget
        self.loading_widget = self._createLoadingWidget()
        self.content_stack.addWidget(self.loading_widget)

        self.setLayout(layout)

        # Connect calendar signals
        self.calendar.clicked.connect(self.updateTaskList)
        self.calendar.currentPageChanged.connect(self.highlightDatesWithTasks)

        # Update task list for current date when widget is initialized
        self.updateTaskList(self.calendar.selectedDate())
        self.updateRepeatedTasksList()

        # Set smooth scrolling for repeated tasks list
        self.repeated_tasks_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.repeated_tasks_list.setHorizontalScrollMode(QListWidget.ScrollPerPixel)

        # Check and add scheduled tasks
        self.checkAndAddScheduledTasks()

    def _createLoadingWidget(self):
        """Create and return a loading widget with animation."""
        loading_widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        loading_label = QLabel()
        movie = QMovie(get_image_path("loading.gif"))
        loading_label.setMovie(movie)
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setFixedSize(50, 50)

        text_label = QLabel("Refreshing schedule...")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet(
            """
            QLabel {
                color: #666;
                font-size: 12px;
                margin-top: 5px;
            }
        """
        )

        layout.addWidget(loading_label)
        layout.addWidget(text_label)
        loading_widget.setLayout(layout)

        # Store movie reference to control it later
        loading_widget.movie = movie

        return loading_widget

    def loadScheduledTasks(self):
        """Load scheduled tasks from the tasks file."""
        self.scheduled_tasks = []
        tasks_file = get_database_path("tasks.json")
        schedule_file = get_database_path("scheduled_tasks.json")

        if (
            not self.main_app
            or not hasattr(self.main_app, "current_user")
            or not self.main_app.current_user
        ):
            return

        try:
            # Load tasks from tasks.json
            with open(tasks_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                for task in data.get("tasks", []):
                    if (
                        task["username"] == self.main_app.current_user
                        and task.get("schedule", "None").lower() != "none"
                    ):
                        self.scheduled_tasks.append(task)
                        print(
                            f"Loaded scheduled task: {task['name']} with schedule {task['schedule']}"
                        )
        except FileNotFoundError:
            with open(tasks_file, "w", encoding="utf-8") as file:
                json.dump({"tasks": []}, file, indent=2)
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in tasks file")

        try:
            # Load tasks from scheduled_tasks.json
            with open(schedule_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                for task in data.get("scheduled_tasks", []):
                    if task["username"] == self.main_app.current_user:
                        if not any(
                            t["name"] == task["name"]
                            and t["start_time"] == task["start_time"]
                            for t in self.scheduled_tasks
                        ):
                            self.scheduled_tasks.append(task)
                            print(
                                f"Loaded scheduled task: {task['name']} with schedule {task['schedule']}"
                            )
        except FileNotFoundError:
            with open(schedule_file, "w", encoding="utf-8") as file:
                json.dump({"scheduled_tasks": []}, file, indent=2)
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in scheduled tasks file")

        # Highlight dates with tasks
        self.highlightDatesWithTasks()

    def refreshSchedule(self):
        """Refresh the schedule by reloading tasks with loading animation."""
        # Show loading widget
        self.content_stack.setCurrentWidget(self.loading_widget)
        self.loading_widget.movie.start()

        # Use timer to delay the refresh operation
        QTimer.singleShot(1000, self._performRefresh)

    def _performRefresh(self):
        """Perform the actual refresh operation."""
        # Reload tasks
        self.loadScheduledTasks()

        # Update current view
        if self.view_selector.currentText() == "Schedule":
            self.updateTaskList(self.calendar.selectedDate())
        else:
            # Untuk Repeated Tasks, hanya update tampilan tanpa menambah task baru
            self.updateRepeatedTasksList()

        # Switch back to appropriate widget
        if self.view_selector.currentText() == "Schedule":
            self.content_stack.setCurrentWidget(self.content_stack.widget(0))
        else:
            self.content_stack.setCurrentWidget(self.content_stack.widget(1))

    def highlightDatesWithTasks(self):
        """Highlight dates that have scheduled tasks."""

        tasks_file = get_database_path("tasks.json")
        schedule_file = get_database_path("scheduled_tasks.json")

        # Reset all dates to default color
        self.calendar.setDateTextFormat(QDate(), self.calendar.dateTextFormat(QDate()))

        # Get current month and year
        current_date = self.calendar.selectedDate()
        current_month = current_date.month()
        current_year = current_date.year()

        # Create a set of dates that have tasks
        dates_with_tasks = set()

        # Get current date
        today = QDate.currentDate()

        # Highlight current date with light blue
        today_format = self.calendar.dateTextFormat(today)
        today_format.setBackground(QBrush(QColor("#ADD8E6")))  # Light blue - lebih kuat
        self.calendar.setDateTextFormat(today, today_format)

        if (
            not self.main_app
            or not hasattr(self.main_app, "current_user")
            or not self.main_app.current_user
        ):
            # print("No current user found for highlighting dates")
            return

        try:
            # print(f"Reading tasks.json for user: {self.main_app.current_user}")
            with open(tasks_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                for task in data.get("tasks", []):
                    if task["username"] == self.main_app.current_user:
                        start_time = task["start_time"]
                        if not start_time or start_time == "None":
                            continue

                        try:
                            start_datetime = datetime.strptime(
                                start_time, "%Y-%m-%d %H:%M"
                            )
                            task_date = QDate(
                                start_datetime.year,
                                start_datetime.month,
                                start_datetime.day,
                            )

                            # Add the date to the set if it's in the current month
                            if (
                                task_date.month() == current_month
                                and task_date.year() == current_year
                            ):
                                dates_with_tasks.add(task_date)
                                print(
                                    f"Added date with task: {task_date.toString('yyyy-MM-dd')}"
                                )

                        except (ValueError, TypeError) as e:
                            print(f"Error processing task: {e}")

        except FileNotFoundError:
            print("tasks.json not found")
            pass

        # Apply highlighting to dates with tasks
        format = self.calendar.dateTextFormat(QDate())
        format.setBackground(QBrush(QColor("#FFE5B4")))  # Light yellow - lebih kuat

        for date in dates_with_tasks:
            # Don't override the current date highlight
            if date != today:
                self.calendar.setDateTextFormat(date, format)
                print(
                    f"Applied yellow highlight to date: {date.toString('yyyy-MM-dd')}"
                )

        # print(f"Total dates with tasks: {len(dates_with_tasks)}")

    def updateTaskList(self, date):
        """Update the task list when a date is selected."""
        self.task_list.clear()

        tasks_file = get_database_path("tasks.json")
        schedule_file = get_database_path("scheduled_tasks.json")

        if (
            not self.main_app
            or not hasattr(self.main_app, "current_user")
            or not self.main_app.current_user
        ):
            return

        try:
            with open(tasks_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                for task in data.get("tasks", []):
                    if task["username"] == self.main_app.current_user:
                        task_dict = {
                            "name": task["name"],
                            "description": task["description"],
                            "start_time": task["start_time"],
                            "deadline": task["deadline"],
                            "priority": task["priority"],
                            "reminder": task["reminder"],
                            "status": task["status"],
                            "schedule": task["schedule"],
                            "username": task["username"],
                        }

                        # Check and update task status based on deadline
                        if task_dict["status"].lower().startswith("due"):
                            try:
                                deadline = datetime.strptime(
                                    task_dict["deadline"], "%Y-%m-%d %H:%M"
                                )
                                current = datetime.now()
                                if current > deadline:
                                    task_dict["status"] = "failed"
                                    # Update the task status in tasks.json
                                    self._updateTaskStatusInFile(task_dict)
                            except Exception as e:
                                print(f"Error checking deadline: {e}")

                        print(
                            f"Found task: {task_dict['name']} with start time: {task_dict['start_time']}"
                        )

                        # Check if task belongs to selected date
                        start_time = task_dict["start_time"]
                        if not start_time or start_time == "None":
                            continue

                        try:
                            start_datetime = datetime.strptime(
                                start_time, "%Y-%m-%d %H:%M"
                            )
                            task_date = QDate(
                                start_datetime.year,
                                start_datetime.month,
                                start_datetime.day,
                            )

                            print(
                                f"Task date: {task_date.toString('yyyy-MM-dd')}, Selected date: {date.toString('yyyy-MM-dd')}"
                            )

                            # Show task if it matches the selected date
                            if task_date == date:
                                print(f"Adding task to list: {task_dict['name']}")
                                # Create task item
                                item = QListWidgetItem()

                                # Create task widget
                                task_widget = QFrame()
                                task_widget.setStyleSheet(
                                    """
                                    QFrame {
                                        background-color: white;
                                        border-radius: 8px;
                                        padding: 8px;
                                        margin: 3px;
                                    }
                                """
                                )

                                # Create layout
                                task_layout = QVBoxLayout(task_widget)
                                task_layout.setContentsMargins(5, 5, 5, 5)
                                task_layout.setSpacing(3)

                                # Task name
                                name_label = QLabel(task_dict["name"])
                                name_label.setFont(QFont("Arial", 14, QFont.Bold))
                                name_label.setMinimumHeight(25)
                                task_layout.addWidget(name_label)

                                # Task description
                                if (
                                    task_dict["description"]
                                    and task_dict["description"] != "None"
                                ):
                                    desc_label = QLabel(task_dict["description"])
                                    desc_label.setStyleSheet(
                                        "color: #666; font-size: 14px;"
                                    )
                                    desc_label.setWordWrap(True)
                                    desc_label.setMinimumHeight(30)
                                    task_layout.addWidget(desc_label)

                                # Task time
                                time_layout = QHBoxLayout()
                                time_layout.setSpacing(10)

                                if (
                                    task_dict["start_time"]
                                    and task_dict["start_time"] != "None"
                                ):
                                    start_time = datetime.strptime(
                                        task_dict["start_time"], "%Y-%m-%d %H:%M"
                                    )
                                    start_time_str = start_time.strftime("%H:%M")
                                    start_label = QLabel(f"Start: {start_time_str}")
                                    start_label.setStyleSheet("font-size: 14px;")
                                    start_label.setMinimumHeight(20)
                                    time_layout.addWidget(start_label)

                                if (
                                    task_dict["deadline"]
                                    and task_dict["deadline"] != "None"
                                ):
                                    deadline = datetime.strptime(
                                        task_dict["deadline"], "%Y-%m-%d %H:%M"
                                    )
                                    deadline_str = deadline.strftime("%H:%M")
                                    deadline_label = QLabel(f"Deadline: {deadline_str}")
                                    deadline_label.setStyleSheet("font-size: 14px;")
                                    deadline_label.setMinimumHeight(20)
                                    time_layout.addWidget(deadline_label)

                                task_layout.addLayout(time_layout)

                                # Task priority and status
                                info_layout = QHBoxLayout()
                                info_layout.setSpacing(5)

                                # Priority
                                priority = task_dict["priority"]
                                priority_colors = {
                                    "High": "#FF4444",
                                    "Medium": "#FF8C00",
                                    "Low": "#FFD700",
                                    "None": "#999",
                                }

                                priority_label = QLabel(priority)
                                priority_label.setStyleSheet(
                                    f"""
                                    background-color: {priority_colors.get(priority, "#999")};
                                    color: white;
                                    border-radius: 8px;
                                    padding: 3px 8px;
                                    font-size: 14px;
                                """
                                )
                                priority_label.setMinimumHeight(20)
                                info_layout.addWidget(priority_label)

                                # Status
                                status = task_dict["status"]
                                status_colors = {
                                    "done": "#4CAF50",
                                    "failed": "#FF4444",
                                    "due": "#999999",
                                }

                                status_text = (
                                    "done"
                                    if "done" in status.lower()
                                    else (
                                        "failed"
                                        if "failed" in status.lower()
                                        else "due"
                                    )
                                )
                                status_label = QLabel(status_text)
                                status_label.setStyleSheet(
                                    f"""
                                    background-color: {status_colors.get(status_text, "#999999")};
                                    color: white;
                                    border-radius: 8px;
                                    padding: 3px 8px;
                                    font-weight: bold;
                                    font-size: 14px;
                                """
                                )
                                status_label.setMinimumHeight(20)
                                info_layout.addWidget(status_label)

                                # Schedule type if exists
                                if (
                                    task_dict["schedule"]
                                    and task_dict["schedule"].lower() != "none"
                                ):
                                    schedule_label = QLabel(
                                        task_dict["schedule"].capitalize()
                                    )
                                    schedule_label.setStyleSheet(
                                        """
                                        background-color: #00B4D8;
                                        color: white;
                                        border-radius: 8px;
                                        padding: 3px 8px;
                                        font-size: 14px;
                                    """
                                    )
                                    schedule_label.setMinimumHeight(20)
                                    info_layout.addWidget(schedule_label)

                                task_layout.addLayout(info_layout)

                                # Set item widget
                                item.setSizeHint(task_widget.sizeHint())
                                self.task_list.addItem(item)
                                self.task_list.setItemWidget(item, task_widget)

                        except (ValueError, TypeError) as e:
                            print(f"Error processing task: {e}")

        except FileNotFoundError:
            print("tasks.json not found")
            pass

    def _updateTaskStatusInFile(self, task_dict):
        """Update task status in tasks.json file."""
        tasks_file = get_database_path("tasks.json")
        try:
            # Read all tasks
            with open(tasks_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                for task in data.get("tasks", []):
                    if (
                        task["name"] == task_dict["name"]
                        and task["description"] == task_dict["description"]
                        and task["start_time"] == task_dict["start_time"]
                        and task["deadline"] == task_dict["deadline"]
                        and task["priority"] == task_dict["priority"]
                        and task["reminder"] == task_dict["reminder"]
                        and task["schedule"] == task_dict["schedule"]
                        and task["username"] == task_dict["username"]
                    ):
                        # Update the status
                        task["status"] = task_dict["status"]

            # Save updated tasks
            with open(tasks_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)

        except Exception as e:
            print(f"Error updating task status in file: {e}")

    def checkAndAddScheduledTasks(self):
        """Check and add scheduled tasks based on schedule."""
        tasks_file = get_database_path("tasks.json")
        schedule_file = get_database_path("scheduled_tasks.json")

        if (
            not self.main_app
            or not hasattr(self.main_app, "current_user")
            or not self.main_app.current_user
        ):
            return

        current_date = datetime.now()
        current_day = current_date.day
        current_weekday = current_date.weekday()  # 0 = Monday, 6 = Sunday

        try:
            # Read scheduled tasks
            with open(schedule_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                scheduled_tasks = data.get("scheduled_tasks", [])

            # Process each scheduled task
            for task in scheduled_tasks:
                if task["username"] != self.main_app.current_user:
                    continue

                schedule = task.get("schedule", "").lower()
                if not schedule or schedule == "none":
                    continue

                last_run = datetime.strptime(task["last_run_date"], "%Y-%m-%d").date()
                current = current_date.date()

                should_run = False
                if schedule == "daily" and last_run < current:
                    should_run = True
                elif schedule == "weekly" and (current - last_run).days >= 7:
                    should_run = True
                elif (
                    schedule == "monthly"
                    and current_day == 1
                    and last_run.month < current.month
                ):
                    should_run = True

                if should_run:
                    # Create new task instance
                    new_task = task.copy()
                    new_task["start_time"] = current_date.strftime("%Y-%m-%d %H:%M")
                    new_task["status"] = "due"

                    # Add to tasks.json
                    try:
                        with open(tasks_file, "r", encoding="utf-8") as file:
                            tasks_data = json.load(file)
                    except (FileNotFoundError, json.JSONDecodeError):
                        tasks_data = {"tasks": []}

                    tasks_data["tasks"].append(new_task)

                    with open(tasks_file, "w", encoding="utf-8") as file:
                        json.dump(tasks_data, file, indent=2)

                    # Update last run date
                    task["last_run_date"] = current_date.strftime("%Y-%m-%d")

            # Save updated scheduled tasks
            with open(schedule_file, "w", encoding="utf-8") as file:
                json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

            # Refresh the display
            self.loadScheduledTasks()

        except Exception as e:
            print(f"Error checking scheduled tasks: {e}")

    def _addTaskToFile(self, task):
        """Add a new task to tasks.json."""
        tasks_file = get_database_path("tasks.json")

        try:
            # Read existing tasks
            try:
                with open(tasks_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {"tasks": []}

            # Add new task
            data["tasks"].append(task)

            # Save updated tasks
            with open(tasks_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)

        except Exception as e:
            print(f"Error adding task to file: {e}")

    def deleteScheduledTask(self, task):
        """Delete a task from scheduled_tasks.json."""
        # Add confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete Scheduled Task",
            "Are you sure you want to delete this scheduled task? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.No:
            return

        schedule_file = get_database_path("scheduled_tasks.json")

        try:
            # Read scheduled tasks
            with open(schedule_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                scheduled_tasks = data.get("scheduled_tasks", [])

            # Remove matching task
            scheduled_tasks = [
                t
                for t in scheduled_tasks
                if not (t["name"] == task["name"] and t["username"] == task["username"])
            ]

            # Save updated tasks
            with open(schedule_file, "w", encoding="utf-8") as file:
                json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

            # Show success message
            QMessageBox.information(
                self,
                "Success",
                "Scheduled task has been deleted successfully!"
            )

            # Refresh the schedule display
            self.refreshSchedule()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete scheduled task: {str(e)}"
            )

    def switchView(self, view_name):
        """Switch between calendar and repeated tasks views."""
        if view_name == "Schedule":
            self.content_stack.setCurrentIndex(0)
            self.updateTaskList(self.calendar.selectedDate())
        else:
            self.content_stack.setCurrentIndex(1)
            self.updateRepeatedTasksList()

    def updateRepeatedTasksList(self):
        """Update the list of repeated tasks."""
        self.repeated_tasks_list.clear()

        schedule_file = get_database_path("scheduled_tasks.json")

        try:
            with open(schedule_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                scheduled_tasks = data.get("scheduled_tasks", [])

            for task in scheduled_tasks:
                if task["username"] == self.main_app.current_user:
                    self._addTaskToRepeatedList(task)

        except FileNotFoundError:
            with open(schedule_file, "w", encoding="utf-8") as file:
                json.dump({"scheduled_tasks": []}, file, indent=2)
        except Exception as e:
            print(f"Error updating repeated tasks list: {e}")

    def _addTaskToRepeatedList(self, task_dict):
        # Create task item
        item = QListWidgetItem()
        
        # Create task widget
        task_widget = QFrame()
        task_widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                margin: 5px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #f5f5f5;
            }
        """)

        # Create main layout
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        # Left side - Task info
        info_layout = QVBoxLayout()
        name_label = QLabel(task_dict["name"])
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        desc_label = QLabel(task_dict.get("description", ""))
        desc_label.setStyleSheet("color: #666;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        top_layout.addLayout(info_layout, stretch=2)

        # Middle - Times layout
        times_layout = QVBoxLayout()
        if task_dict["start_time"] and task_dict["start_time"] != "None":
            start_time = datetime.strptime(task_dict["start_time"], "%Y-%m-%d %H:%M")
            start_time_str = start_time.strftime("%H:%M")
            start_label = QLabel(f"StartLine: {start_time_str}")
            times_layout.addWidget(start_label)

        if task_dict["deadline"] and task_dict["deadline"] != "None":
            deadline = datetime.strptime(task_dict["deadline"], "%Y-%m-%d %H:%M")
            deadline_str = deadline.strftime("%H:%M")
            deadline_label = QLabel(f"Deadline: {deadline_str}")
            times_layout.addWidget(deadline_label)

        top_layout.addLayout(times_layout, stretch=1)

        # Right side container for schedule, priority and status
        right_container = QVBoxLayout()
        right_container.setSpacing(0)
        right_container.setContentsMargins(0, 0, 0, 0)
        
        # Add schedule info if exists
        schedule = task_dict.get("schedule", "")
        if schedule:
            schedule_label = QLabel(f"🔄scheduled: {schedule}")
            schedule_label.setStyleSheet("color: #666; font-size: 14px;")
            schedule_label.setContentsMargins(0, 8, 0, 8)
            schedule_label.setFixedHeight(32)
            schedule_label.setMinimumWidth(120)
            schedule_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            right_container.addWidget(schedule_label)
        
        # Create container for priority, status and kebab menu
        buttons_container = QWidget()
        buttons_container.setStyleSheet("background-color: white;")
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)
        
        # Add priority and status buttons
        priority_status_layout = QHBoxLayout()
        priority_status_layout.setSpacing(5)
        priority_status_layout.setContentsMargins(0, 0, 0, 0)

        # Priority button
        priority = task_dict.get("priority", "None")
        priority_colors = {
            "High": "#FF4444",
            "Medium": "#FF8C00",
            "Low": "#FFD700",
            "None": "#999999"
        }
        priority_btn = QPushButton(priority)
        priority_btn.setFixedWidth(80)
        priority_btn.setFixedHeight(32)
        priority_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {priority_colors.get(priority, "#999999")};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 5px;
                font-size: 12px;
            }}
        """)
        priority_status_layout.addWidget(priority_btn)

        # Status button
        status = task_dict.get("status", "due")
        status_text = "done" if "done" in status.lower() else "failed" if "failed" in status.lower() else "due"
        status_colors = {
            "done": "#4CAF50",
            "failed": "#FF4444",
            "due": "#999999"
        }
        status_btn = QPushButton(status_text)
        status_btn.setFixedWidth(80)
        status_btn.setFixedHeight(32)
        status_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {status_colors.get(status_text, "#999999")};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 5px;
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        priority_status_layout.addWidget(status_btn)
        
        # Add kebab menu
        kebab_btn = QPushButton()
        kebab_btn.setIcon(QIcon(get_image_path("kebab.png")))
        kebab_btn.setIconSize(QSize(16, 16))
        kebab_btn.setFixedSize(32, 32)
        kebab_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 16px;
                padding: 8px;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #E3F8FF;
            }
        """)

        # Create kebab menu
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #E3F8FF;
                color: #00B4D8;
            }
        """)

        # Add menu actions
        actions = [
            ("Delete Schedule", get_image_path("delete.png")),
        ]

        for text, icon_path in actions:
            action = QAction(QIcon(icon_path), text, self)
            action.triggered.connect(lambda checked, t=task_dict: self.deleteScheduledTask(t))
            menu.addAction(action)

        kebab_btn.clicked.connect(
            lambda: menu.exec_(kebab_btn.mapToGlobal(kebab_btn.rect().bottomLeft()))
        )
        
        # Add layouts to buttons container
        buttons_layout.addLayout(priority_status_layout)
        buttons_layout.addWidget(kebab_btn)
        
        # Add buttons container to right container
        right_container.addWidget(buttons_container)
        
        # Add right container to top layout
        top_layout.addLayout(right_container)

        main_layout.addLayout(top_layout)
        task_widget.setLayout(main_layout)

        # Set item widget
        item.setSizeHint(task_widget.sizeHint())
        self.repeated_tasks_list.addItem(item)
        self.repeated_tasks_list.setItemWidget(item, task_widget)

    def show_add_repeated_task_dialog(self):
        """Show the dialog for adding a new repeated task."""
        schedule_file = get_database_path("scheduled_tasks.json")

        try:
            # Membuka addRepeataed task dialog
            dialog = AddRepeatedTaskDialog(self)

            if dialog.exec_():
                try:
                    task_data = dialog.get_task_data()

                    #Validasi nama repeated task
                    if not task_data["name"]:
                        QMessageBox.warning(self, "Error", "Task Name is required!")
                        return
                    
                    try:
                        start_time = datetime.strptime(task_data["start_time"], "%H:%M").time()
                    except ValueError:
                        QMessageBox.warning(self, "Error", "Invalid time fomat!")
                    
                    #menginisiasi dengan current date dan time
                    current_date = datetime.now()
                    start_datetime = datetime.combine(current_date.date(), start_time)
                    
                    #->ototmatis mengset deadline pada 23:59 di hari yang sama
                    deadline_time = datetime.combine(current_date.date(), datetime.strptime("23:59","%H:%M").time())


                    # Create task dari data yang diinput
                    form_task = {
                        "name": task_data["name"],
                        "description": task_data["description"],
                        "start_time": start_datetime.strftime("%Y-%m-%d %H:%M"),
                        "deadline": deadline_time.strftime("%Y-%m-%d %H:%M"),
                        "priority": task_data["priority"],
                        "reminder": "None",
                        "status": "due",
                        "schedule": task_data["schedule"],
                        "username" : self.main_app.current_user
                    }

                    #validasi seluruh fields yang harus diisi
                    required_fields = ["name", "start_time", "deadline", "priority", "schedule", "username"]
                    for field in required_fields:
                        if not form_task.get(field):
                            QMessageBox.warning(self, "Error", f"Missing required field: {field}")
                            return
                
                    #baca data lama
                    try : 
                        with open(schedule_file, "r", encoding="utf-8") as file:
                            data = json.load(file)
                            scheduled_tasks = data.get("scheduled_tasks", [])
                    except (FileNotFoundError, json.JSONDecodeError) as e:
                        scheduled_tasks = []

                    #tambah task baru ke dalam dict
                    scheduled_tasks.append(form_task)

                    #tambah data ke dalam file schedule_task.txt
                    with open (schedule_file, "w", encoding="utf-8") as file :
                        json.dump({"scheduled_tasks":scheduled_tasks}, file, indent=2)

                    QMessageBox.information(self, " Succes", "Task saved to database")

                    #updatet isi halaman
                    self.updateRepeatedTasksList()


                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error processing task data: {str(e)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"failed opening dialog: {str(e)}")


    def eventFilter(self, obj, event):
        """Event filter to detect when dropdown is opened/closed."""
        if obj == self.view_selector.view() and event.type() == event.Show:
            self.arrow_label.setText("▲")
        elif obj == self.view_selector.view() and event.type() == event.Hide:
            self.arrow_label.setText("▼")
        return super().eventFilter(obj, event)

    def clearAllScheduledTasks(self):
        """Clear all scheduled tasks after user confirmation."""
        schedule_file = get_database_path("scheduled_tasks.json")

        reply = QMessageBox.question(
            self,
            "Clear All Scheduled Tasks",
            "Are you sure you want to clear all scheduled tasks? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                # Read all tasks
                with open(schedule_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    scheduled_tasks = data.get("scheduled_tasks", [])

                # Keep only tasks from other users
                scheduled_tasks = [
                    task
                    for task in scheduled_tasks
                    if task["username"] != self.main_app.current_user
                ]

                # Save updated tasks
                with open(schedule_file, "w", encoding="utf-8") as file:
                    json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

                # Refresh the display
                self.loadScheduledTasks()
                self.updateRepeatedTasksList()

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to clear scheduled tasks: {str(e)}"
                )


class AddRepeatedTaskDialog(QDialog):
    """Dialog for adding a new repeated task."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Repeated Task")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Task name
        name_layout = QVBoxLayout()
        name_label = QLabel("Task Name:")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter task name")
        self.name_edit.setStyleSheet(
            """
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00B4D8;
            }
        """
        )
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Task description
        desc_layout = QVBoxLayout()
        desc_label = QLabel("Description:")
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.setPlaceholderText("Enter task description")
        self.desc_edit.setStyleSheet(
            """
            QTextEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border: 1px solid #00B4D8;
            }
        """
        )
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)
        layout.addLayout(desc_layout)

        # Start time
        time_layout = QVBoxLayout()
        time_label = QLabel("Start Time:")
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setStyleSheet(
            """
            QTimeEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QTimeEdit:focus {
                border: 1px solid #00B4D8;
            }
        """
        )
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_edit)
        layout.addLayout(time_layout)

        # Schedule type
        schedule_layout = QVBoxLayout()
        schedule_label = QLabel("Repeat:")
        self.schedule_combo = QComboBox()
        self.schedule_combo.addItems(["Daily", "Weekly", "Monthly"])
        self.schedule_combo.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 1px solid #00B4D8;
            }
        """
        )
        schedule_layout.addWidget(schedule_label)
        schedule_layout.addWidget(self.schedule_combo)
        layout.addLayout(schedule_layout)

        # Day selection for weekly tasks
        self.weekly_container = QWidget()
        weekly_layout = QVBoxLayout(self.weekly_container)
        weekly_day_label = QLabel("Select Day:")
        self.weekly_day_combo = QComboBox()
        self.weekly_day_combo.addItems(
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
        )
        self.weekly_day_combo.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 1px solid #00B4D8;
            }
        """
        )
        weekly_layout.addWidget(weekly_day_label)
        weekly_layout.addWidget(self.weekly_day_combo)
        self.weekly_container.setVisible(False)
        layout.addWidget(self.weekly_container)

        # Date selection for monthly tasks
        self.monthly_container = QWidget()
        monthly_layout = QVBoxLayout(self.monthly_container)
        monthly_date_label = QLabel("Select Date:")
        self.monthly_date_combo = QComboBox()
        self.monthly_date_combo.addItems([str(i) for i in range(1, 32)])
        self.monthly_date_combo.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 1px solid #00B4D8;
            }
        """
        )
        monthly_layout.addWidget(monthly_date_label)
        monthly_layout.addWidget(self.monthly_date_combo)
        self.monthly_container.setVisible(False)
        layout.addWidget(self.monthly_container)

        # Connect schedule type change
        self.schedule_combo.currentTextChanged.connect(self.on_schedule_type_changed)

        # Priority
        priority_layout = QVBoxLayout()
        priority_label = QLabel("Priority:")
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["High", "Medium", "Low"])
        self.priority_combo.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 1px solid #00B4D8;
            }
        """
        )
        priority_layout.addWidget(priority_label)
        priority_layout.addWidget(self.priority_combo)
        layout.addLayout(priority_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Add Task")
        self.ok_button.setStyleSheet(
            """
            QPushButton {
                background-color: #00B4D8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0096B7;
            }
        """
        )
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """
        )
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def on_schedule_type_changed(self, schedule_type):
        """Handle schedule type change to show/hide appropriate selection widgets."""
        self.weekly_container.setVisible(schedule_type == "Weekly")
        self.monthly_container.setVisible(schedule_type == "Monthly")

    def get_task_data(self):
        """Return the task data entered by the user."""
        schedule_type = self.schedule_combo.currentText().lower()
        schedule_data = schedule_type

        if schedule_type == "weekly":
            schedule_data = f"weekly_{self.weekly_day_combo.currentText().lower()}"
        elif schedule_type == "monthly":
            schedule_data = f"monthly_{self.monthly_date_combo.currentText()}"

        return {
            "name": self.name_edit.text(),
            "description": self.desc_edit.toPlainText(),
            "start_time": self.time_edit.time().toString("HH:mm"),
            "schedule": schedule_data,
            "priority": self.priority_combo.currentText(),
        }

    def addRepeatedTask(self):
        """Add a new repeated task."""
        try:
            dialog = AddRepeatedTaskDialog(self)
            if dialog.exec_():
                try:
                    task_data = dialog.get_task_data()

                    # Validate task data
                    if not task_data["name"]:
                        QMessageBox.warning(self, "Error", "Task name is required.")
                        return

                    # Validate time format
                    try:
                        start_time = datetime.strptime(
                            task_data["start_time"], "%H:%M"
                        ).time()
                    except ValueError:
                        QMessageBox.warning(self, "Error", "Invalid time format.")
                        return

                    # Create the task with current date and time
                    current_date = datetime.now()
                    start_datetime = datetime.combine(current_date.date(), start_time)

                    # Set deadline to 23:59 of the same day
                    deadline_datetime = datetime.combine(
                        current_date.date(), datetime.strptime("23:59", "%H:%M").time()
                    )

                    # Create the task
                    task = {
                        "name": task_data["name"],
                        "description": task_data["description"],
                        "start_time": start_datetime.strftime("%Y-%m-%d %H:%M"),
                        "deadline": deadline_datetime.strftime(
                            "%Y-%m-%d %H:%M"
                        ),  # Set to 23:59
                        "priority": task_data["priority"],
                        "reminder": "None",
                        "status": "due",
                        "schedule": task_data["schedule"],
                        "username": self.main_app.current_user,
                    }

                    # Validate all required fields
                    required_fields = [
                        "name",
                        "start_time",
                        "deadline",
                        "priority",
                        "schedule",
                        "username",
                    ]
                    for field in required_fields:
                        if not task.get(field):
                            QMessageBox.warning(
                                self, "Error", f"Missing required field: {field}"
                            )
                            return

                    # Add task to scheduled_tasks.json
                    schedule_file = get_database_path("scheduled_tasks.json")
                    try:
                        with open(schedule_file, "r", encoding="utf-8") as file:
                            data = json.load(file)
                            scheduled_tasks = data.get("scheduled_tasks", [])
                    except (FileNotFoundError, json.JSONDecodeError):
                        scheduled_tasks = []

                    task["is_active"] = True
                    task["last_run_date"] = task["start_time"].split()[0]
                    scheduled_tasks.append(task)

                    with open(schedule_file, "w", encoding="utf-8") as file:
                        json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

                    # Refresh the display
                    self.updateRepeatedTasksList()
                    QMessageBox.information(
                        self, "Success", "Task has been added successfully."
                    )

                except Exception as e:
                    QMessageBox.critical(
                        self, "Error", f"Error processing task data: {str(e)}"
                    )

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to create task dialog: {str(e)}"
            )
            print(f"Error in addRepeatedTask: {str(e)}")  # For debugging
