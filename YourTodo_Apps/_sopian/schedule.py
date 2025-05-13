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
from _sopian.repeatedTask import AddRepeatedTaskDialog, RepeatedTaskManager


class ScheduleWidget(QWidget):
    """
    Widget yang menampilkan jadwal tugas dalam tampilan kalender.
    Memungkinkan melihat dan mengelola tugas terjadwal.
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
        """Inisialisasi komponen UI widget jadwal."""
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

        # Dropdown pemilih tampilan
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

        # Hilangkan pendekatan custom widget
        self.view_selector.setEditable(False)
        self.view_selector.setInsertPolicy(QComboBox.NoInsert)

        # Buat tombol custom dengan panah
        dropdown_container = QWidget()
        dropdown_layout = QHBoxLayout(dropdown_container)
        dropdown_layout.setContentsMargins(0, 0, 0, 0)
        dropdown_layout.setSpacing(0)

        # Tambahkan combo box ke layout
        dropdown_layout.addWidget(self.view_selector)

        # Buat label untuk panah
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

        # Tambahkan label panah ke layout
        dropdown_layout.addWidget(self.arrow_label)

        # Tambahkan container ke header
        header.addWidget(dropdown_container)

        # Hubungkan sinyal untuk mengubah arah panah
        self.view_selector.view().installEventFilter(self)
        self.view_selector.currentTextChanged.connect(self.switchView)

        # Tombol refresh
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

        # Stack konten untuk berpindah antar tampilan
        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)

        # Widget kalender
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
        """Membuat widget loading dengan animasi."""
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
        """Memuat tugas yang dijadwalkan dari file tugas."""
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
            # Memuat tugas dari tasks.json
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
            # Memuat tugas dari scheduled_tasks.json
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
        """Memperbarui jadwal dengan memuat tugas kembali dengan animasi loading."""
        # Tampilkan widget loading
        self.content_stack.setCurrentWidget(self.loading_widget)
        self.loading_widget.movie.start()

        # Gunakan timer untuk menunda operasi refresh
        QTimer.singleShot(500, self._performRefresh)

    def _performRefresh(self):
        """Melakukan operasi refresh aktual."""
        # Muat ulang tugas
        self.loadScheduledTasks()

        # Update tampilan saat ini
        if self.view_selector.currentText() == "Schedule":
            self.updateTaskList(self.calendar.selectedDate())
        else:
            # Untuk tugas berulang, hanya update tampilan tanpa menambah tugas baru
            self.updateRepeatedTasksList()

        # Kembali ke tampilan yang sesuai
        if self.view_selector.currentText() == "Schedule":
            self.content_stack.setCurrentWidget(self.content_stack.widget(0))
        else:
            self.content_stack.setCurrentWidget(self.content_stack.widget(1))

    def highlightDatesWithTasks(self):
        """Menandai tanggal yang memiliki tugas yang dijadwalkan."""

        tasks_file = get_database_path("tasks.json")
        schedule_file = get_database_path("scheduled_tasks.json")

        # Atur semua tanggal ke warna default
        self.calendar.setDateTextFormat(QDate(), self.calendar.dateTextFormat(QDate()))

        # Dapatkan bulan dan tahun saat ini
        current_date = self.calendar.selectedDate()
        current_month = current_date.month()
        current_year = current_date.year()

        # Buat set tanggal yang memiliki tugas
        dates_with_tasks = set()

        # Dapatkan tanggal saat ini
        today = QDate.currentDate()

        # Highlight tanggal saat ini dengan warna biru yang lebih kuat
        today_format = self.calendar.dateTextFormat(today)
        today_format.setBackground(QBrush(QColor("#ADD8E6")))  # Light blue - lebih kuat
        self.calendar.setDateTextFormat(today, today_format)

        if (
            not self.main_app
            or not hasattr(self.main_app, "current_user")
            or not self.main_app.current_user
        ):
            # print("Tidak ada pengguna saat ini untuk menandai tanggal")
            return

        try:
            # print(f"Membaca tasks.json untuk pengguna: {self.main_app.current_user}")
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

                            # Tambahkan tanggal ke set jika berada dalam bulan saat ini
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

        # Terapkan penandai ke tanggal yang memiliki tugas
        format = self.calendar.dateTextFormat(QDate())
        format.setBackground(QBrush(QColor("#FFE5B4")))  # Light yellow - lebih kuat

        for date in dates_with_tasks:
            # Jangan override penandai tanggal saat ini
            if date != today:
                self.calendar.setDateTextFormat(date, format)
                print(
                    f"Applied yellow highlight to date: {date.toString('yyyy-MM-dd')}"
                )

        # print(f"Total dates with tasks: {len(dates_with_tasks)}")

    def updateTaskList(self, date):
        """Memperbarui daftar tugas saat tanggal dipilih."""
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

                        # Periksa dan perbarui status tugas berdasarkan batas waktu
                        if task_dict["status"].lower().startswith("due"):
                            try:
                                deadline_str = task_dict["deadline"]
                                if deadline_str and deadline_str != "None":
                                    deadline = datetime.strptime(
                                        deadline_str, "%Y-%m-%d %H:%M"
                                    )
                                    current = datetime.now()
                                    if current > deadline:
                                        task_dict["status"] = "failed"
                                        # Update status tugas dalam tasks.json
                                        self._updateTaskStatusInFile(task_dict)
                            except Exception as e:
                                print(f"Error checking deadline: {e}")

                        print(
                            f"Found task: {task_dict['name']} with start time: {task_dict['start_time']}"
                        )

                        # Periksa apakah tugas terkait dengan tanggal yang dipilih
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

                            # Tampilkan tugas jika sesuai dengan tanggal yang dipilih
                            if task_date == date:
                                print(f"Menambahkan tugas ke daftar: {task_dict['name']}")
                                # Buat item tugas
                                item = QListWidgetItem()

                                # Buat widget tugas
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

                                # Buat layout
                                task_layout = QVBoxLayout(task_widget)
                                task_layout.setContentsMargins(5, 5, 5, 5)
                                task_layout.setSpacing(3)

                                # Nama tugas
                                name_label = QLabel(task_dict["name"])
                                name_label.setFont(QFont("Arial", 14, QFont.Bold))
                                name_label.setMinimumHeight(25)
                                task_layout.addWidget(name_label)

                                # Deskripsi tugas
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

                                # Waktu tugas
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
                                    try:
                                        deadline = datetime.strptime(
                                            task_dict["deadline"], "%Y-%m-%d %H:%M"
                                        )
                                        deadline_str = deadline.strftime("%H:%M")
                                        deadline_label = QLabel(f"Deadline: {deadline_str}")
                                        deadline_label.setStyleSheet("font-size: 14px;")
                                        deadline_label.setMinimumHeight(20)
                                        time_layout.addWidget(deadline_label)
                                    except Exception as e:
                                        print(f"Error processing deadline: {e}")

                                task_layout.addLayout(time_layout)

                                # Prioritas tugas dan status
                                info_layout = QHBoxLayout()
                                info_layout.setSpacing(5)

                                # Prioritas
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

                                # Jenis jadwal jika ada
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
        """Memperbarui status tugas dalam file tasks.json."""
        tasks_file = get_database_path("tasks.json")
        try:
            # Baca semua tugas
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
        """Memeriksa dan menambahkan tugas berdasarkan jadwal."""
        RepeatedTaskManager.checkAndAddScheduledTasks(self)

    def _addTaskToFile(self, task):
        """Menambahkan tugas baru ke tasks.json."""
        RepeatedTaskManager._addTaskToFile(task)

    def deleteScheduledTask(self, task):
        """Delete a task from scheduled_tasks.json."""
        RepeatedTaskManager.deleteScheduledTask(self, task)

    def switchView(self, view_name):
        """Switch between calendar and repeated tasks view."""
        if view_name == "Schedule":
            self.content_stack.setCurrentIndex(0)
            self.updateTaskList(self.calendar.selectedDate())
        else:
            self.content_stack.setCurrentIndex(1)
            self.updateRepeatedTasksList()

    def updateRepeatedTasksList(self):
        """Memperbarui daftar tugas berulang."""
        RepeatedTaskManager.updateRepeatedTasksList(self)

    def show_add_repeated_task_dialog(self):
        """Tampilkan dialog untuk menambahkan tugas berulang baru."""
        AddRepeatedTaskDialog.addRepeatedTask(self)

    def eventFilter(self, obj, event):
        """Event filter untuk mendeteksi ketika dropdown terbuka/ditutup."""
        if obj == self.view_selector.view() and event.type() == event.Show:
            self.arrow_label.setText("▲")
        elif obj == self.view_selector.view() and event.type() == event.Hide:
            self.arrow_label.setText("▼")
        return super().eventFilter(obj, event)

    def clearAllScheduledTasks(self):
        """Clear All Schedule task."""
        RepeatedTaskManager.clearAllScheduledTasks(self)

    def _addTaskToRepeatedList(self, task_dict):
        """Add task to repeated list."""
        RepeatedTaskManager._addTaskToRepeatedList(self, task_dict)
