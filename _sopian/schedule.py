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
from _sopian.main_components import TaskItemWidget


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

    def initUI(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        self.title = QLabel("Schedule")
        self.title.setFont(QFont("Arial", 20, QFont.Bold))
        self.title.setStyleSheet("color: #333;")
        header.addWidget(self.title)
        header.addStretch()

        # Ganti dengan dua tombol untuk pemilihan tampilan
        view_buttons_container = QWidget()
        view_buttons_layout = QHBoxLayout(view_buttons_container)
        view_buttons_layout.setContentsMargins(0, 0, 0, 0)
        view_buttons_layout.setSpacing(10)  # Jarak antar tombol

        # Tombol Schedule
        self.schedule_btn = QPushButton("Schedule")
        self.schedule_btn.setCheckable(True)
        self.schedule_btn.setChecked(True)
        self.schedule_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 3px 10px;
                font-weight: bold;
                font-size: 12px;
                min-width: 90px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
            QPushButton:checked {
                background-color: #E3F8FF;
                color: #00B4D8;
                border: 1px solid #00B4D8;
            }
        """
        )
        self.schedule_btn.clicked.connect(lambda: self.switchView("Schedule"))

        # Tombol Repeated Tasks
        self.repeated_tasks_btn = QPushButton("Repeated Tasks")
        self.repeated_tasks_btn.setCheckable(True)
        self.repeated_tasks_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 3px 10px;
                font-weight: bold;
                font-size: 12px;
                min-width: 90px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
            QPushButton:checked {
                background-color: #E3F8FF;
                color: #00B4D8;
                border: 1px solid #00B4D8;
            }
        """
        )
        self.repeated_tasks_btn.clicked.connect(lambda: self.switchView("Repeated Tasks"))

        # Tambahkan tombol ke layout
        view_buttons_layout.addWidget(self.schedule_btn)
        view_buttons_layout.addWidget(self.repeated_tasks_btn)
        view_buttons_layout.addSpacing(20)  # Mengurangi jarak dengan tombol refresh

        # Tambahkan container ke header
        header.addWidget(view_buttons_container)

        # Tombol refresh
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet(
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
        self.refresh_btn.clicked.connect(self.refreshSchedule)
        header.addWidget(self.refresh_btn)

        main_layout.addLayout(header)

        # Stack konten untuk berpindah antar tampilan
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

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
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.setStyleSheet(
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
        self.clear_all_btn.clicked.connect(self.clearAllScheduledTasks)
        repeated_layout.addWidget(self.clear_all_btn)

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

        # Set the main layout
        self.setLayout(main_layout)

        # Load tasks and update count immediately
        self.loadScheduledTasks()
        self.updateTaskList(QDate.currentDate())
        self.updateRepeatedTasksList()
        
        # Update task count immediately after loading tasks
        if hasattr(self, 'main_app') and hasattr(self.main_app, 'updateTaskCount'):
            self.main_app.updateTaskCount()

        # Connect calendar signals
        self.calendar.clicked.connect(self.updateTaskList)
        self.calendar.currentPageChanged.connect(self.highlightDatesWithTasks)

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

        # jika tidak atribut current user tidak ada (menghindari akses tanpa username)
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
                        # memastikan tidak ada task yang sudah ditambahkan pada task.json dari schedule_task.json
                        if not any(
                            t["name"] == task["name"]
                            and t["start_time"] == task["start_time"]
                            for t in self.scheduled_tasks
                        ):
                            self.scheduled_tasks.append(task)

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
        RepeatedTaskManager.checkAndAddScheduledTasks(self)

        # Update tampilan saat ini
        if self.schedule_btn.isChecked():
            self.updateTaskList(self.calendar.selectedDate())
        else:
            # Untuk tugas berulang, hanya update tampilan tanpa menambah tugas baru
            self.updateRepeatedTasksList()

        # Kembali ke tampilan yang sesuai
        if self.schedule_btn.isChecked():
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

                            # Tampilkan tugas jika sesuai dengan tanggal yang dipilih
                            if task_date == date:
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
                                        deadline_label = QLabel(
                                            f"Deadline: {deadline_str}"
                                        )
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
                                    # Get only the schedule type (daily/weekly/monthly)
                                    schedule_type = task_dict["schedule"].split("_")[0].capitalize()
                                    schedule_label = QLabel(schedule_type)
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
        """Switch between calendar and repeated tasks views."""
        if view_name == "Schedule":
            self.content_stack.setCurrentWidget(self.content_stack.widget(0))
            self.schedule_btn.setChecked(True)
            self.repeated_tasks_btn.setChecked(False)
        elif view_name == "Repeated Tasks":
            self.content_stack.setCurrentWidget(self.content_stack.widget(1))
            self.schedule_btn.setChecked(False)
            self.repeated_tasks_btn.setChecked(True)
            # Load repeated tasks immediately when switching to this view
            self.loadScheduledTasks()
            self.updateRepeatedTasksList()
        
        self.updateTaskList(self.calendar.selectedDate())

    def updateRepeatedTasksList(self):
        """Memperbarui daftar tugas berulang."""
        RepeatedTaskManager.updateRepeatedTasksList(self)

    def show_add_repeated_task_dialog(self):
        """Tampilkan dialog untuk menambahkan tugas berulang baru."""
        AddRepeatedTaskDialog.addRepeatedTask(self)

    def clearAllScheduledTasks(self):
        """Clear All Schedule task."""
        RepeatedTaskManager.clearAllScheduledTasks(self)

    def _addTaskToRepeatedList(self, task_dict):
        """Add task to repeated list."""
        RepeatedTaskManager._addTaskToRepeatedList(self, task_dict)

    def filter_tasks_by_query(self, query):
        """Show/hide scheduled tasks in the list based on search query (matches name or description, case-insensitive)."""
        query = query.strip().lower()
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            widget = self.task_list.itemWidget(item)
            # Find name and description labels
            name = ""
            desc = ""
            for j in range(widget.layout().count()):
                child = widget.layout().itemAt(j).widget()
                if isinstance(child, QLabel):
                    if not name:
                        name = child.text().lower()
                    else:
                        desc = child.text().lower()
                        break
            if not query or query in name or query in desc:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def _find_all_labels(self, layout):
        """Recursively find all QLabel widgets in a layout."""
        labels = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget()
            if widget and isinstance(widget, QLabel):
                labels.append(widget)
            elif item.layout():
                labels.extend(self._find_all_labels(item.layout()))
        return labels

    def filter_repeated_tasks_by_query(self, query):
        """Show/hide repeated tasks in the list based on search query (matches name or description, case-insensitive)."""
        query = query.strip().lower()
        for i in range(self.repeated_tasks_list.count()):
            item = self.repeated_tasks_list.item(i)
            widget = self.repeated_tasks_list.itemWidget(item)
            # Recursively find all QLabel widgets
            labels = self._find_all_labels(widget.layout()) if widget else []
            name = labels[0].text().lower() if len(labels) > 0 else ""
            desc = labels[1].text().lower() if len(labels) > 1 else ""
            if not query or query in name or query in desc:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def update_text(self, key, new_text):
        """Update text when language changes"""
        # Update schedule-related text
        if key == "schedule":
            if hasattr(self, "title"):
                self.title.setText(new_text)

        # Update view selector text
        if hasattr(self, "schedule_btn"):
            self.schedule_btn.setText(new_text)
        if hasattr(self, "repeated_tasks_btn"):
            self.repeated_tasks_btn.setText(new_text)

        # Update task items
        if hasattr(self, "task_list_layout"):
            for i in range(self.task_list_layout.count()):
                widget = self.task_list_layout.itemAt(i).widget()
                if isinstance(widget, TaskItemWidget):
                    widget.update_text(key, new_text)

        # Update filter combo box
        if hasattr(self, "filter_combo"):
            if key == "all_tasks":
                self.filter_combo.setItemText(0, new_text)
            elif key == "high_priority":
                self.filter_combo.setItemText(1, new_text)
            elif key == "medium_priority":
                self.filter_combo.setItemText(2, new_text)
            elif key == "low_priority":
                self.filter_combo.setItemText(3, new_text)
            elif key == "completed":
                self.filter_combo.setItemText(4, new_text)
            elif key == "pending":
                self.filter_combo.setItemText(5, new_text)

        #updaet button
        if hasattr (self, "refresh_btn"):
            self.refresh_btn.setText(new_text)

        if hasattr (self, "clear_all_btn"):
            self.clear_all_btn.setText(new_text)
            
            
