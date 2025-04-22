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
)
from PyQt5.QtGui import QFont, QColor, QPalette, QBrush, QMovie
from PyQt5.QtCore import Qt, QDate, QDateTime, QTimer, QTime
import os
from datetime import datetime, timedelta
import calendar
from path_utils import get_image_path, get_database_path


class ScheduleWidget(QWidget):
    """
    Widget that displays the task schedule in a calendar view.
    Allows viewing and managing scheduled tasks.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Pastikan parent adalah instance dari ToDoApp
        if parent and hasattr(parent, 'current_user'):
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
        self.view_selector.setStyleSheet("""
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
        """)
        
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
        self.arrow_label.setStyleSheet("""
            color: #333;
            font-size: 14px;
            font-weight: bold;
            padding-right: 5px;
        """)
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
        refresh_btn.setStyleSheet("""
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
        """)
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
        self.calendar.setStyleSheet("""
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
        """)
        # Set fixed size for calendar
        self.calendar.setFixedHeight(250)
        calendar_layout.addWidget(self.calendar)

        # Task list for selected date
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("""
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
        """)
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
        add_task_btn.setStyleSheet("""
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
        """)
        add_task_btn.clicked.connect(self.show_add_repeated_task_dialog)
        repeated_layout.addWidget(add_task_btn)
        
        # Add Clear All button
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.setStyleSheet("""
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
        """)
        clear_all_btn.clicked.connect(self.clearAllScheduledTasks)
        repeated_layout.addWidget(clear_all_btn)
        
        self.repeated_tasks_list = QListWidget()
        self.repeated_tasks_list.setStyleSheet("""
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
        """)
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
        loading_label.setFixedSize(50, 50)  # Set fixed size for loading animation

        text_label = QLabel("Refreshing schedule...")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                margin-top: 5px;
            }
        """)

        layout.addWidget(loading_label)
        layout.addWidget(text_label)
        loading_widget.setLayout(layout)
        
        # Store movie reference to control it later
        loading_widget.movie = movie
        
        return loading_widget

    def loadScheduledTasks(self):
        """Load scheduled tasks from the tasks file."""
        self.scheduled_tasks = []
        tasks_file = get_database_path("tasks.txt")
        schedule_file = get_database_path("scheduled_tasks.txt")

        if not self.main_app or not hasattr(self.main_app, 'current_user') or not self.main_app.current_user:
            return
            
        try:
            with open(tasks_file, "r", encoding="utf-8") as file:
                for line in file:
                    data = line.strip().split(" | ")
                    if len(data) >= 9 and data[8] == self.main_app.current_user:
                        # Check if task has a schedule
                        schedule = data[7]
                        if schedule and schedule.lower() != "none":
                            task_dict = {
                                "name": data[0],
                                "description": data[1],
                                "start_time": data[2],
                                "deadline": data[3],
                                "priority": data[4],
                                "reminder": data[5],
                                "status": data[6],
                                "schedule": schedule,
                                "username": data[8]
                            }
                            self.scheduled_tasks.append(task_dict)
                            print(f"Loaded scheduled task: {task_dict['name']} with schedule {task_dict['schedule']}")
        except FileNotFoundError:
            pass
            
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

        tasks_file = get_database_path("tasks.txt")
        schedule_file = get_database_path("scheduled_tasks.txt")

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
        
        if not self.main_app or not hasattr(self.main_app, 'current_user') or not self.main_app.current_user:
            print("No current user found for highlighting dates")
            return
            
        try:
            print(f"Reading tasks.txt for user: {self.main_app.current_user}")
            with open(tasks_file, "r", encoding="utf-8") as file:
                for line in file:
                    data = line.strip().split(" | ")
                    if len(data) >= 9 and data[8] == self.main_app.current_user:
                        start_time = data[2]
                        if not start_time or start_time == "None":
                            continue
                            
                        try:
                            start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
                            task_date = QDate(start_datetime.year, start_datetime.month, start_datetime.day)
                            
                            # Add the date to the set if it's in the current month
                            if task_date.month() == current_month and task_date.year() == current_year:
                                dates_with_tasks.add(task_date)
                                print(f"Added date with task: {task_date.toString('yyyy-MM-dd')}")
                        
                        except (ValueError, TypeError) as e:
                            print(f"Error processing task: {e}")
        
        except FileNotFoundError:
            print("tasks.txt not found")
            pass
        
        # Apply highlighting to dates with tasks
        format = self.calendar.dateTextFormat(QDate())
        format.setBackground(QBrush(QColor("#FFE5B4")))  # Light yellow - lebih kuat
        
        for date in dates_with_tasks:
            # Don't override the current date highlight
            if date != today:
                self.calendar.setDateTextFormat(date, format)
                print(f"Applied yellow highlight to date: {date.toString('yyyy-MM-dd')}")
        
        print(f"Total dates with tasks: {len(dates_with_tasks)}")

    def updateTaskList(self, date):
        """Update the task list when a date is selected."""
        self.task_list.clear()
        
        tasks_file = get_database_path("tasks.txt")
        schedule_file = get_database_path("scheduled_tasks.txt")

        if not self.main_app or not hasattr(self.main_app, 'current_user') or not self.main_app.current_user:
            return
            
        try:
            with open(tasks_file, "r", encoding="utf-8") as file:
                for line in file:
                    data = line.strip().split(" | ")
                    if len(data) >= 9 and data[8] == self.main_app.current_user:
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
                        
                        # Check and update task status based on deadline
                        if task_dict["status"].lower().startswith("due"):
                            try:
                                deadline = datetime.strptime(task_dict["deadline"], "%Y-%m-%d %H:%M")
                                current = datetime.now()
                                if current > deadline:
                                    task_dict["status"] = "failed"
                                    # Update the task status in tasks.txt
                                    self._updateTaskStatusInFile(task_dict)
                            except Exception as e:
                                print(f"Error checking deadline: {e}")
                        
                        print(f"Found task: {task_dict['name']} with start time: {task_dict['start_time']}")
                        
                        # Check if task belongs to selected date
                        start_time = task_dict["start_time"]
                        if not start_time or start_time == "None":
                            continue
                            
                        try:
                            start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
                            task_date = QDate(start_datetime.year, start_datetime.month, start_datetime.day)
                            
                            print(f"Task date: {task_date.toString('yyyy-MM-dd')}, Selected date: {date.toString('yyyy-MM-dd')}")
                            
                            # Show task if it matches the selected date
                            if task_date == date:
                                print(f"Adding task to list: {task_dict['name']}")
                                # Create task item
                                item = QListWidgetItem()
                                
                                # Create task widget
                                task_widget = QFrame()
                                task_widget.setStyleSheet("""
                                    QFrame {
                                        background-color: white;
                                        border-radius: 8px;
                                        padding: 8px;
                                        margin: 3px;
                                    }
                                """)
                                
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
                                if task_dict["description"] and task_dict["description"] != "None":
                                    desc_label = QLabel(task_dict["description"])
                                    desc_label.setStyleSheet("color: #666; font-size: 14px;")
                                    desc_label.setWordWrap(True)
                                    desc_label.setMinimumHeight(30)
                                    task_layout.addWidget(desc_label)
                                
                                # Task time
                                time_layout = QHBoxLayout()
                                time_layout.setSpacing(10)
                                
                                if task_dict["start_time"] and task_dict["start_time"] != "None":
                                    start_time = datetime.strptime(task_dict["start_time"], "%Y-%m-%d %H:%M")
                                    start_time_str = start_time.strftime("%H:%M")
                                    start_label = QLabel(f"Start: {start_time_str}")
                                    start_label.setStyleSheet("font-size: 14px;")
                                    start_label.setMinimumHeight(20)
                                    time_layout.addWidget(start_label)
                                
                                if task_dict["deadline"] and task_dict["deadline"] != "None":
                                    deadline = datetime.strptime(task_dict["deadline"], "%Y-%m-%d %H:%M")
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
                                priority_label.setStyleSheet(f"""
                                    background-color: {priority_colors.get(priority, "#999")};
                                    color: white;
                                    border-radius: 8px;
                                    padding: 3px 8px;
                                    font-size: 14px;
                                """)
                                priority_label.setMinimumHeight(20)
                                info_layout.addWidget(priority_label)
                                
                                # Status
                                status = task_dict["status"]
                                status_colors = {
                                    "done": "#4CAF50",
                                    "failed": "#FF4444",
                                    "due": "#999999",
                                }
                                
                                status_text = "done" if "done" in status.lower() else "failed" if "failed" in status.lower() else "due"
                                status_label = QLabel(status_text)
                                status_label.setStyleSheet(f"""
                                    background-color: {status_colors.get(status_text, "#999999")};
                                    color: white;
                                    border-radius: 8px;
                                    padding: 3px 8px;
                                    font-weight: bold;
                                    font-size: 14px;
                                """)
                                status_label.setMinimumHeight(20)
                                info_layout.addWidget(status_label)
                                
                                # Schedule type if exists
                                if task_dict["schedule"] and task_dict["schedule"].lower() != "none":
                                    schedule_label = QLabel(task_dict["schedule"].capitalize())
                                    schedule_label.setStyleSheet("""
                                        background-color: #00B4D8;
                                        color: white;
                                        border-radius: 8px;
                                        padding: 3px 8px;
                                        font-size: 14px;
                                    """)
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
            print("tasks.txt not found")
            pass 

    def _updateTaskStatusInFile(self, task_dict):
        """Update task status in tasks.txt file."""
        tasks_file = get_database_path("tasks.txt")
        schedule_file = get_database_path("scheduled_tasks.txt")
        try:
            # Read all tasks
            all_tasks = []
            with open(tasks_file, "r", encoding="utf-8") as file:
                for line in file:
                    data = line.strip().split(" | ")
                    if len(data) >= 9:
                        # If this is the task we want to update
                        if (data[0] == task_dict["name"] and 
                            data[1] == task_dict["description"] and 
                            data[2] == task_dict["start_time"] and 
                            data[3] == task_dict["deadline"] and 
                            data[4] == task_dict["priority"] and 
                            data[5] == task_dict["reminder"] and 
                            data[7] == task_dict["schedule"] and 
                            data[8] == task_dict["username"]):
                            # Update the status
                            data[6] = task_dict["status"]
                        all_tasks.append(" | ".join(data))
            
            # Write back all tasks
            with open(tasks_file, "w", encoding="utf-8") as file:
                for task_str in all_tasks:
                    file.write(task_str + "\n")
                    
        except Exception as e:
            print(f"Error updating task status in file: {e}")

    def checkAndAddScheduledTasks(self):
        """Periksa dan tambahkan task terjadwal berdasarkan jadwal."""

        tasks_file = get_database_path("tasks.txt")
        schedule_file = get_database_path("scheduled_tasks.txt")

        if not self.main_app or not hasattr(self.main_app, 'current_user') or not self.main_app.current_user:
            return
            
        current_date = datetime.now()
        current_day = current_date.day
        current_weekday = current_date.weekday()  # 0 = Senin, 6 = Minggu
        
        try:
            # Baca task terjadwal
            scheduled_tasks = []
            with open(schedule_file, "r", encoding="utf-8") as file:
                for line in file:
                    if line.startswith('#'):  # Skip komentar
                        scheduled_tasks.append(line)
                        continue
                        
                    data = line.strip().split(" | ")
                    if len(data) >= 9 and data[8] == self.main_app.current_user:
                        task_dict = {
                            "name": data[0],
                            "description": data[1],
                            "start_time": data[2],
                            "deadline": data[3],
                            "priority": data[4],
                            "reminder": data[5],
                            "status": data[6],
                            "schedule": data[7],
                            "username": data[8],
                            "isAdded": data[9] if len(data) > 9 else "False",  # Default ke False jika tidak ada
                            "lastAddedDate": data[10] if len(data) > 10 else ""  # Tambahkan field untuk tracking tanggal terakhir ditambahkan
                        }
                        
                        # Periksa apakah task perlu ditambahkan berdasarkan jadwal
                        should_add = False
                        
                        try:
                            schedule_type = task_dict["schedule"].split("_")[0]
                            
                            # Untuk daily task, reset isAdded jika ini hari baru
                            if schedule_type == "daily":
                                today_str = current_date.strftime("%Y-%m-%d")
                                if task_dict["lastAddedDate"] != today_str:
                                    task_dict["isAdded"] = "False"
                                    task_dict["lastAddedDate"] = today_str
                                should_add = True
                                
                            elif schedule_type == "weekly":
                                # Task mingguan ditambahkan setiap hari yang sama dalam minggu
                                selected_day = task_dict["schedule"].split("_")[1]
                                days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                                if days[current_weekday] == selected_day:
                                    should_add = True
                                    
                            elif schedule_type == "monthly":
                                # Task bulanan ditambahkan setiap tanggal yang sama dalam bulan
                                selected_date = int(task_dict["schedule"].split("_")[1])
                                if current_day == selected_date:
                                    should_add = True
                                    
                        except (ValueError, TypeError) as e:
                            print(f"Error parsing schedule: {e}")
                            continue
                        
                        # Jika task perlu ditambahkan dan belum ditambahkan hari ini
                        if should_add and task_dict["isAdded"] == "False":
                            # Buat task baru dengan tanggal hari ini
                            new_task = self._createNewScheduledTask(task_dict, current_date)
                            if new_task:
                                self._addTaskToFile(new_task)
                                task_dict["isAdded"] = "True"
                                print(f"Added scheduled task: {new_task['name']}")
                        
                        # Tambahkan task ke list untuk ditulis kembali
                        task_str = f"{task_dict['name']} | {task_dict['description']} | {task_dict['start_time']} | {task_dict['deadline']} | {task_dict['priority']} | {task_dict['reminder']} | {task_dict['status']} | {task_dict['schedule']} | {task_dict['username']} | {task_dict['isAdded']} | {task_dict['lastAddedDate']}"
                        scheduled_tasks.append(task_str+"\n")
                    else:
                        scheduled_tasks.append(line)
            
            # Tulis kembali semua task dengan status isAdded yang diperbarui
            with open(schedule_file, "w", encoding="utf-8") as file:
                for task_str in scheduled_tasks:
                    file.write(task_str)
        
        except FileNotFoundError:
            # Jika file tidak ada, buat file baru
            with open(schedule_file, "w", encoding="utf-8") as file:
                pass
        except Exception as e:
            print(f"Error checking scheduled tasks: {e}")
    
    def _createNewScheduledTask(self, original_task, current_date):
        """Buat task baru berdasarkan task asli dengan tanggal saat ini."""
        try:
            # Parse waktu asli
            original_start = datetime.strptime(original_task["start_time"], "%Y-%m-%d %H:%M")
            original_deadline = datetime.strptime(original_task["deadline"], "%Y-%m-%d %H:%M")
            
            # Hitung selisih waktu antara start dan deadline
            time_diff = original_deadline - original_start
            
            # Buat waktu start baru dengan tanggal hari ini
            new_start = datetime(
                current_date.year, 
                current_date.month, 
                current_date.day,
                original_start.hour,
                original_start.minute
            )
            
            # Buat deadline baru dengan menambahkan selisih waktu
            new_deadline = new_start + time_diff
            
            # Buat task baru
            new_task = {
                "name": original_task["name"],
                "description": original_task["description"],
                "start_time": new_start.strftime("%Y-%m-%d %H:%M"),
                "deadline": new_deadline.strftime("%Y-%m-%d %H:%M"),
                "priority": original_task["priority"],
                "reminder": original_task["reminder"],
                "status": "due",  # Status baru selalu "due"
                "schedule": original_task["schedule"],  # Preserve the original schedule type
                "username": original_task["username"]
            }
            
            return new_task
            
        except (ValueError, TypeError) as e:
            print(f"Error creating new scheduled task: {e}")
            return None
    
    def _addTaskToFile(self, task):
        """Tambahkan task baru ke tasks.txt."""

        tasks_file = get_database_path("tasks.txt")
        schedule_file = get_database_path("scheduled_tasks.txt")

        try:
            # Baca semua task yang ada
            all_tasks = []
            try:
                with open(tasks_file, "r", encoding="utf-8") as file:
                    for line in file:
                        all_tasks.append(line.strip())
            except FileNotFoundError:
                pass
            
            # Buat string task baru
            new_task_str = f"{task['name']} | {task['description']} | {task['start_time']} | {task['deadline']} | {task['priority']} | {task['reminder']} | {task['status']} | {task['schedule']} | {task['username']}"
            
            # Tambahkan task baru
            all_tasks.append(new_task_str)
            
            # Tulis kembali ke file
            with open(tasks_file, "w", encoding="utf-8") as file:
                for task_str in all_tasks:
                    file.write(task_str + "\n")
                    
        except Exception as e:
            print(f"Error adding task to file: {e}") 

    def deleteScheduledTask(self, task):
        """Delete a task from scheduled_tasks.txt."""

        tasks_file = get_database_path("tasks.txt")
        schedule_file = get_database_path("scheduled_tasks.txt")

        try:
            # Read all scheduled tasks
            scheduled_tasks = []
            try:
                with open(schedule_file, "r", encoding="utf-8") as file:
                    for line in file:
                        if line.startswith('#'):  # Keep comments
                            scheduled_tasks.append(line.strip())
                            continue
                            
                        data = line.strip().split(" | ")
                        if len(data) >= 9:
                            # Keep tasks that don't match the one to delete
                            if not (data[0] == task["name"] and 
                                   data[1] == task["description"] and 
                                   data[2] == task["start_time"] and 
                                   data[3] == task["deadline"] and 
                                   data[4] == task["priority"] and 
                                   data[5] == task["reminder"] and 
                                   data[6] == task["status"] and 
                                   data[7] == task["schedule"] and 
                                   data[8] == task["username"]):
                                scheduled_tasks.append(line.strip())
            except FileNotFoundError:
                return
                
            # Write back all tasks except the deleted one
            with open(schedule_file, "w", encoding="utf-8") as file:
                for task_str in scheduled_tasks:
                    file.write(task_str + "\n")
                    
            # Refresh the schedule display
            self.refreshSchedule()
            
        except Exception as e:
            print(f"Error deleting scheduled task: {e}") 

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

        tasks_file = get_database_path("tasks.txt")
        schedule_file = get_database_path("scheduled_tasks.txt")
        
        if not self.main_app or not hasattr(self.main_app, 'current_user') or not self.main_app.current_user:
            return
            
        try:
            with open(schedule_file, "r", encoding="utf-8") as file:
                for line in file:
                    if line.startswith('#'):  # Skip comments
                        continue
                        
                    data = line.strip().split(" | ")
                    if len(data) >= 9 and data[8] == self.main_app.current_user:
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
                        
                        # Create task item
                        item = QListWidgetItem()
                        
                        # Create task widget
                        task_widget = QFrame()
                        task_widget.setStyleSheet("""
                            QFrame {
                                background-color: white;
                                border-radius: 8px;
                                padding: 8px;
                                margin: 3px;
                            }
                        """)
                        
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
                        if task_dict["description"] and task_dict["description"] != "None":
                            desc_label = QLabel(task_dict["description"])
                            desc_label.setStyleSheet("color: #666; font-size: 14px;")
                            desc_label.setWordWrap(True)
                            desc_label.setMinimumHeight(30)
                            task_layout.addWidget(desc_label)
                        
                        # Task time
                        time_layout = QHBoxLayout()
                        time_layout.setSpacing(10)
                        
                        if task_dict["start_time"] and task_dict["start_time"] != "None":
                            start_time = datetime.strptime(task_dict["start_time"], "%Y-%m-%d %H:%M")
                            start_time_str = start_time.strftime("%H:%M")
                            start_label = QLabel(f"Start: {start_time_str}")
                            start_label.setStyleSheet("font-size: 14px;")
                            start_label.setMinimumHeight(20)
                            time_layout.addWidget(start_label)
                        
                        if task_dict["deadline"] and task_dict["deadline"] != "None":
                            deadline = datetime.strptime(task_dict["deadline"], "%Y-%m-%d %H:%M")
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
                        priority_label.setStyleSheet(f"""
                            background-color: {priority_colors.get(priority, "#999")};
                            color: white;
                            border-radius: 8px;
                            padding: 3px 8px;
                            font-size: 14px;
                        """)
                        priority_label.setMinimumHeight(20)
                        info_layout.addWidget(priority_label)
                        
                        # Status
                        status = task_dict["status"]
                        status_colors = {
                            "done": "#4CAF50",
                            "failed": "#FF4444",
                            "due": "#999999",
                        }
                        
                        status_text = "done" if "done" in status.lower() else "failed" if "failed" in status.lower() else "due"
                        status_label = QLabel(status_text)
                        status_label.setStyleSheet(f"""
                            background-color: {status_colors.get(status_text, "#999999")};
                            color: white;
                            border-radius: 8px;
                            padding: 3px 8px;
                            font-weight: bold;
                            font-size: 14px;
                        """)
                        status_label.setMinimumHeight(20)
                        info_layout.addWidget(status_label)
                        
                        # Schedule type
                        schedule_label = QLabel(task_dict["schedule"].capitalize())
                        schedule_label.setStyleSheet("""
                            background-color: #00B4D8;
                            color: white;
                            border-radius: 8px;
                            padding: 3px 8px;
                            font-size: 14px;
                        """)
                        schedule_label.setMinimumHeight(20)
                        info_layout.addWidget(schedule_label)
                        
                        task_layout.addLayout(info_layout)
                        
                        # Delete button in a separate row for better visibility
                        delete_layout = QHBoxLayout()
                        delete_layout.setAlignment(Qt.AlignRight)
                        
                        delete_btn = QPushButton("Delete Schedule")
                        delete_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #FF5252;
                                color: white;
                                border: none;
                                border-radius: 8px;
                                padding: 8px 15px;
                                font-size: 16px;
                                font-weight: bold;
                                min-width: 120px;
                            }
                            QPushButton:hover {
                                background-color: #FF1744;
                            }
                            QPushButton:pressed {
                                background-color: #D50000;
                            }
                        """)
                        delete_btn.setCursor(Qt.PointingHandCursor)
                        delete_btn.clicked.connect(lambda checked, t=task_dict: self.deleteScheduledTask(t))
                        delete_layout.addWidget(delete_btn)
                        
                        task_layout.addLayout(delete_layout)
                        
                        # Set item widget
                        item.setSizeHint(task_widget.sizeHint())
                        self.repeated_tasks_list.addItem(item)
                        self.repeated_tasks_list.setItemWidget(item, task_widget)
                        
        except FileNotFoundError:
            pass

    def show_add_repeated_task_dialog(self):
        """Show the dialog for adding a new repeated task."""

        tasks_file = get_database_path("tasks.txt")
        schedule_file = get_database_path("scheduled_tasks.txt")

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
                        start_time = datetime.strptime(task_data["start_time"], "%H:%M").time()
                    except ValueError:
                        QMessageBox.warning(self, "Error", "Invalid time format.")
                        return
                        
                    # Create the task with current date and time
                    current_date = datetime.now()
                    start_datetime = datetime.combine(current_date.date(), start_time)
                    
                    # Set deadline to 23:59 of the same day
                    deadline_datetime = datetime.combine(current_date.date(), datetime.strptime("23:59", "%H:%M").time())
                    
                    # Create the task
                    task = {
                        "name": task_data["name"],
                        "description": task_data["description"],
                        "start_time": start_datetime.strftime("%Y-%m-%d %H:%M"),
                        "deadline": deadline_datetime.strftime("%Y-%m-%d %H:%M"),  # Set to 23:59
                        "priority": task_data["priority"],
                        "reminder": "None",
                        "status": "due",
                        "schedule": task_data["schedule"],
                        "username": self.main_app.current_user
                    }
                    
                    # Validate all required fields
                    required_fields = ["name", "start_time", "deadline", "priority", "schedule", "username"]
                    for field in required_fields:
                        if not task.get(field):
                            QMessageBox.warning(self, "Error", f"Missing required field: {field}")
                            return
                    
                    # Add task to scheduled_tasks.txt
                    try:
                        with open(schedule_file, "a", encoding="utf-8") as file:
                            task_str = f"{task['name']} | {task['description']} | {task['start_time']} | {task['deadline']} | {task['priority']} | {task['reminder']} | {task['status']} | {task['schedule']} | {task['username']}"
                            file.write(task_str + "\n")
                            
                        # Refresh the repeated tasks list
                        self.updateRepeatedTasksList()
                        
                        # Show success message
                        QMessageBox.information(self, "Success", "Task has been added successfully.")
                        
                    except IOError as e:
                        QMessageBox.critical(self, "Error", f"Failed to write to file: {str(e)}")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to add task: {str(e)}")
                        
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error processing task data: {str(e)}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create task dialog: {str(e)}")
            print(f"Error in show_add_repeated_task_dialog: {str(e)}")  # For debugging

    def eventFilter(self, obj, event):
        """Event filter to detect when dropdown is opened/closed."""
        if obj == self.view_selector.view() and event.type() == event.Show:
            self.arrow_label.setText("▲")
        elif obj == self.view_selector.view() and event.type() == event.Hide:
            self.arrow_label.setText("▼")
        return super().eventFilter(obj, event)

    def clearAllScheduledTasks(self):
        """Clear all scheduled tasks after user confirmation."""
        tasks_file = get_database_path("tasks.txt")
        schedule_file = get_database_path("scheduled_tasks.txt")

        reply = QMessageBox.question(
            self,
            "Clear All Scheduled Tasks",
            "Are you sure you want to clear all scheduled tasks? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Read existing tasks and keep only those not belonging to current user
                remaining_tasks = []
                try:
                    with open(schedule_file, "r", encoding="utf-8") as file:
                        for line in file:
                            if line.startswith('#'):  # Keep header comments
                                remaining_tasks.append(line)
                            else:
                                data = line.strip().split(" | ")
                                if len(data) >= 9 and data[-1] != self.main_app.current_user:
                                    remaining_tasks.append(line)
                except FileNotFoundError:
                    pass

                # Write back only the remaining tasks
                with open(schedule_file, "w", encoding="utf-8") as file:
                    for task in remaining_tasks:
                        file.write(task)

                # Refresh the repeated tasks list
                self.updateRepeatedTasksList()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Success",
                    "All your scheduled tasks have been cleared."
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to clear scheduled tasks: {str(e)}"
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
        self.name_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00B4D8;
            }
        """)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Task description
        desc_layout = QVBoxLayout()
        desc_label = QLabel("Description:")
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.setPlaceholderText("Enter task description")
        self.desc_edit.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border: 1px solid #00B4D8;
            }
        """)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)
        layout.addLayout(desc_layout)
        
        # Start time
        time_layout = QVBoxLayout()
        time_label = QLabel("Start Time:")
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setStyleSheet("""
            QTimeEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QTimeEdit:focus {
                border: 1px solid #00B4D8;
            }
        """)
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_edit)
        layout.addLayout(time_layout)
        
        # Schedule type
        schedule_layout = QVBoxLayout()
        schedule_label = QLabel("Repeat:")
        self.schedule_combo = QComboBox()
        self.schedule_combo.addItems(["Daily", "Weekly", "Monthly"])
        self.schedule_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 1px solid #00B4D8;
            }
        """)
        schedule_layout.addWidget(schedule_label)
        schedule_layout.addWidget(self.schedule_combo)
        layout.addLayout(schedule_layout)
        
        # Day selection for weekly tasks
        self.weekly_container = QWidget()
        weekly_layout = QVBoxLayout(self.weekly_container)
        weekly_day_label = QLabel("Select Day:")
        self.weekly_day_combo = QComboBox()
        self.weekly_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self.weekly_day_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 1px solid #00B4D8;
            }
        """)
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
        self.monthly_date_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 1px solid #00B4D8;
            }
        """)
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
        self.priority_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 1px solid #00B4D8;
            }
        """)
        priority_layout.addWidget(priority_label)
        priority_layout.addWidget(self.priority_combo)
        layout.addLayout(priority_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Add Task")
        self.ok_button.setStyleSheet("""
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
        """)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
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
        """)
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
            "priority": self.priority_combo.currentText()
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
                        start_time = datetime.strptime(task_data["start_time"], "%H:%M").time()
                    except ValueError:
                        QMessageBox.warning(self, "Error", "Invalid time format.")
                        return
                        
                    # Create the task with current date and time
                    current_date = datetime.now()
                    start_datetime = datetime.combine(current_date.date(), start_time)
                    
                    # Set deadline to 23:59 of the same day
                    deadline_datetime = datetime.combine(current_date.date(), datetime.strptime("23:59", "%H:%M").time())
                    
                    # Create the task
                    task = {
                        "name": task_data["name"],
                        "description": task_data["description"],
                        "start_time": start_datetime.strftime("%Y-%m-%d %H:%M"),
                        "deadline": deadline_datetime.strftime("%Y-%m-%d %H:%M"),  # Set to 23:59
                        "priority": task_data["priority"],
                        "reminder": "None",
                        "status": "due",
                        "schedule": task_data["schedule"],
                        "username": self.main_app.current_user
                    }
                    
                    # Validate all required fields
                    required_fields = ["name", "start_time", "deadline", "priority", "schedule", "username"]
                    for field in required_fields:
                        if not task.get(field):
                            QMessageBox.warning(self, "Error", f"Missing required field: {field}")
                            return
                    
                    # Add task to scheduled_tasks.txt
                    schedule_file = get_database_path("scheduled_tasks.txt")
                    try:
                        with open(schedule_file, "a", encoding="utf-8") as file:
                            task_str = f"{task['name']} | {task['description']} | {task['start_time']} | {task['deadline']} | {task['priority']} | {task['reminder']} | {task['status']} | {task['schedule']} | {task['username']}"
                            file.write(task_str + "\n")
                            
                        # Refresh the repeated tasks list
                        self.updateRepeatedTasksList()
                        
                        # Show success message
                        QMessageBox.information(self, "Success", "Task has been added successfully.")
                        
                    except IOError as e:
                        QMessageBox.critical(self, "Error", f"Failed to write to file: {str(e)}")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to add task: {str(e)}")
                        
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error processing task data: {str(e)}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create task dialog: {str(e)}")
            print(f"Error in addRepeatedTask: {str(e)}")  # For debugging