from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QTimeEdit,
    QPushButton,
    QComboBox,
    QWidget,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QMenu,
    QAction,
    QCheckBox,
    QGridLayout,
)
from PyQt5.QtCore import Qt, QTime, QSize
from PyQt5.QtGui import QFont, QIcon
from datetime import datetime
import json
from _sopian.path_utils import get_database_path, get_image_path


class RepeatedTaskManager:
    """Class untuk mengelola tugas berulang"""

    @staticmethod
    def clearAllScheduledTasks(parent):
        """Clear All Schedule task."""
        schedule_file = get_database_path("scheduled_tasks.json")

        reply = QMessageBox.question(
            parent,
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
                    if task["username"] != parent.main_app.current_user
                ]

                # Save updated tasks
                with open(schedule_file, "w", encoding="utf-8") as file:
                    json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

                # Refresh the display
                parent.loadScheduledTasks()
                parent.updateRepeatedTasksList()

            except Exception as e:
                QMessageBox.critical(
                    parent, "Error", f"Failed to clear scheduled tasks: {str(e)}"
                )

    @staticmethod
    def _addTaskToRepeatedList(parent, task_dict):
        # Buat item tugas
        item = QListWidgetItem()

        # Buat widget tugas
        task_widget = QFrame()
        task_widget.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border-radius: 10px;
                margin: 5px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #f5f5f5;
            }
        """
        )

        # Buat layout utama
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        # Sisi kiri - Info tugas
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)  # Menambahkan spacing antara name dan description
        info_layout.setContentsMargins(0, 0, 0, 5) # Menambahkan sedikit margin bawah pada layout info
        
        name_label = QLabel(task_dict["name"])
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        name_label.setWordWrap(True)  # Memastikan text wrap aktif
        name_label.setMinimumHeight(25)  # Mengurangi minimum height sedikit, agar lebih fleksibel
        name_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # Mengatur alignment ke kiri atas
        
        desc_label = QLabel(task_dict.get("description", ""))
        desc_label.setStyleSheet("color: #666;")
        desc_label.setWordWrap(True)  # Memastikan description wrap juga
        desc_label.setContentsMargins(0, 0, 0, 8) # Menambahkan margin bawah pada description label (ditingkatkan)
        desc_label.setAlignment(Qt.AlignTop | Qt.AlignLeft) # Mengatur alignment ke kiri atas
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        top_layout.addLayout(info_layout, stretch=2)

        # Sisi tengah - Layout waktu
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

        # Sisi kanan - Container untuk jadwal, prioritas dan status
        right_container = QVBoxLayout()
        right_container.setSpacing(0)
        right_container.setContentsMargins(0, 0, 0, 0)

        # Add schedule info if exists
        schedule = task_dict.get("schedule", "")
        if schedule:
            # Get only the schedule type (daily/weekly/monthly)
            schedule_type = schedule.split("_")[0].capitalize()
            schedule_label = QLabel(f"🔄scheduled: {schedule_type}")
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
            "None": "#999999",
        }
        priority_btn = QPushButton(priority)
        priority_btn.setFixedWidth(80)
        priority_btn.setFixedHeight(32)
        priority_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {priority_colors.get(priority, "#999999")};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 5px;
                font-size: 12px;
            }}
        """
        )
        priority_status_layout.addWidget(priority_btn)

        # Status button
        status = task_dict.get("status", "due")
        status_text = (
            "done"
            if "done" in status.lower()
            else "failed" if "failed" in status.lower() else "due"
        )
        status_colors = {"done": "#4CAF50", "failed": "#FF4444", "due": "#999999"}
        status_btn = QPushButton(status_text)
        status_btn.setFixedWidth(80)
        status_btn.setFixedHeight(32)
        status_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {status_colors.get(status_text, "#999999")};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 5px;
                font-weight: bold;
                font-size: 12px;
            }}
        """
        )
        priority_status_layout.addWidget(status_btn)

        # Add kebab menu
        kebab_btn = QPushButton()
        kebab_btn.setIcon(QIcon(get_image_path("kebab.png")))
        kebab_btn.setIconSize(QSize(16, 16))
        kebab_btn.setFixedSize(32, 32)
        kebab_btn.setStyleSheet(
            """
            QPushButton {
                border: none;
                border-radius: 16px;
                padding: 8px;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #E3F8FF;
            }
        """
        )

        # Create kebab menu
        menu = QMenu()
        menu.setStyleSheet(
            """
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
        """
        )

        # Add menu actions
        actions = [
            ("Delete Schedule", get_image_path("delete.png")),
        ]

        for text, icon_path in actions:
            action = QAction(QIcon(icon_path), text, parent)
            action.triggered.connect(
                lambda checked, t=task_dict: RepeatedTaskManager.deleteScheduledTask(
                    parent, t
                )
            )
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
        parent.repeated_tasks_list.addItem(item)
        parent.repeated_tasks_list.setItemWidget(item, task_widget)

    @staticmethod
    def updateRepeatedTasksList(parent):
        """Memperbarui daftar tugas berulang."""
        parent.repeated_tasks_list.clear()

        schedule_file = get_database_path("scheduled_tasks.json")

        try:
            with open(schedule_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                scheduled_tasks = data.get("scheduled_tasks", [])

            for task in scheduled_tasks:
                if task["username"] == parent.main_app.current_user:
                    RepeatedTaskManager._addTaskToRepeatedList(parent, task)

        except FileNotFoundError:
            with open(schedule_file, "w", encoding="utf-8") as file:
                json.dump({"scheduled_tasks": []}, file, indent=2)
        except Exception as e:
            print(f"Error updating repeated tasks list: {e}")

    @staticmethod
    def deleteScheduledTask(parent, task):
        """Delete a task from scheduled_tasks.json."""
        # Add confirmation dialog
        reply = QMessageBox.question(
            parent,
            "Delete Scheduled Task",
            "Are you sure you want to delete this scheduled task? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.No:
            return

        schedule_file = get_database_path("scheduled_tasks.json")

        try:
            # membaca shceduled tasks
            with open(schedule_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                scheduled_tasks = data.get("scheduled_tasks", [])

            # Hapus tugas yang sesuai
            scheduled_tasks = [
                t
                for t in scheduled_tasks
                if not (t["name"] == task["name"] and t["username"] == task["username"])
            ]

            # Simpan tugas yang diperbarui
            with open(schedule_file, "w", encoding="utf-8") as file:
                json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

            # Tampilkan pesan sukses
            QMessageBox.information(
                parent, "Success", "Scheduled task has been deleted successfully!"
            )

            # Perbarui tampilan
            parent.refreshSchedule()

        except Exception as e:
            QMessageBox.critical(
                parent, "Error", f"Failed to delete scheduled task: {str(e)}"
            )

    @staticmethod
    def _addTaskToFile(task):
        """Menambahkan tugas baru ke tasks.json."""
        tasks_file = get_database_path("tasks.json")

        try:
            # Baca tugas yang ada
            try:
                with open(tasks_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {"tasks": []}

            # Cek apakah task sudah ada
            task_exists = False
            for existing_task in data["tasks"]:
                # Untuk task terjadwal, cek berdasarkan nama, username, dan tanggal
                if task.get("schedule", "None").lower() != "none":
                    if (
                        existing_task["name"] == task["name"]
                        and existing_task["username"] == task["username"]
                        and existing_task["start_time"].startswith(
                            task["start_time"].split()[0]
                        )
                    ):
                        task_exists = True
                        break
                # Untuk task biasa, cek berdasarkan nama dan username saja
                else:
                    if (
                        existing_task["name"] == task["name"]
                        and existing_task["username"] == task["username"]
                    ):
                        task_exists = True
                        break

            # Tambahkan tugas baru jika belum ada
            if not task_exists:
                data["tasks"].append(task)
                with open(tasks_file, "w", encoding="utf-8") as file:
                    json.dump(data, file, indent=2)
                print(f"Successfully added task: {task['name']} to tasks.json")

        except Exception as e:
            print(f"Error adding task to file: {e}")

    @staticmethod
    def checkAndAddScheduledTasks(parent):
        """Memeriksa dan menambahkan tugas berdasarkan jadwal."""
        if (
            not parent.main_app
            or not hasattr(parent.main_app, "current_user")
            or not parent.main_app.current_user
        ):
            return

        current_date = datetime.now()
        current_day = current_date.day
        current_weekday = current_date.weekday()  # 0 = Senin, 6 = Minggu
        today_str = current_date.strftime("%Y-%m-%d")

        try:
            # Baca task terjadwal dari JSON
            schedule_file = get_database_path("scheduled_tasks.json")
            try:
                with open(schedule_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    scheduled_tasks = data.get("scheduled_tasks", [])
            except (FileNotFoundError, json.JSONDecodeError):
                scheduled_tasks = []

            # Baca tasks.json untuk cek duplikasi
            tasks_file = get_database_path("tasks.json")
            try:
                with open(tasks_file, "r", encoding="utf-8") as file:
                    tasks_data = json.load(file)
                    existing_tasks = tasks_data.get("tasks", [])
            except (FileNotFoundError, json.JSONDecodeError):
                existing_tasks = []

            tasks_updated = False
            for task in scheduled_tasks:
                if task["username"] != parent.main_app.current_user:
                    continue

                try:
                    schedule_type = task["schedule"].split("_")[0]
                    # Initialize is_added with default value from task or False
                    is_added = task.get("is_added", False)

                    # Untuk daily task
                    if schedule_type == "daily":
                        # Cek apakah task sudah ada di tasks.json untuk hari ini
                        task_exists = False
                        for existing_task in existing_tasks:
                            if (
                                existing_task["name"] == task["name"]
                                and existing_task["username"] == task["username"]
                                and existing_task["schedule"] == task["schedule"]
                                and existing_task["start_time"].startswith(today_str)
                            ):
                                task_exists = True
                                break

                        # Jika task belum ada di tasks.json untuk hari ini
                        if not task_exists:
                            # Cek last_run_date
                            last_run = task.get("last_run_date")
                            if last_run and is_added:
                                last_run_date = datetime.strptime(last_run, "%Y-%m-%d")
                                # Jika last_run_date lebih kecil dari current_date, tambahkan task
                                if last_run_date.date() != current_date.date():
                                    is_added = False

                    elif schedule_type == "weekly":
                        # Task mingguan ditambahkan setiap hari yang sama dalam minggu
                        selected_days = task["schedule"].split("_")[1].split(",")
                        last_run = task.get("last_run_date")
                        days = [
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                            "saturday",
                            "sunday",
                        ]
                        
                        if last_run and is_added:
                            last_run_date = datetime.strptime(last_run, "%Y-%m-%d")
                            if current_date.date() != last_run_date.date():
                                if days[current_weekday] in selected_days:
                                    is_added = False

                    elif schedule_type == "monthly":
                        # Task bulanan ditambahkan setiap tanggal yang sama dalam bulan
                        selected_dates = [int(date) for date in task["schedule"].split("_")[1].split(",")]
                        last_run = task.get("last_run_date")
                        if last_run and is_added:
                            last_run_date = datetime.strptime(last_run, "%Y-%m-%d")
                            if current_date.date() != last_run_date.date():
                                if current_day in selected_dates:
                                    is_added = False

                except (ValueError, TypeError) as e:
                    print(f"Error parsing schedule: {e}")
                    continue

                # Jika task perlu ditambahkan
                if not is_added:
                    # Buat task baru dengan tanggal hari ini
                    new_task = RepeatedTaskManager._createNewScheduledTask(
                        task, current_date
                    )
                    if new_task:
                        RepeatedTaskManager._addTaskToFile(new_task)
                        task["last_run_date"] = today_str
                        task["is_added"] = True
                        tasks_updated = True

            # Simpan perubahan ke file jika ada yang diupdate
            if tasks_updated:
                with open(schedule_file, "w", encoding="utf-8") as file:
                    json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

                # Refresh tampilan
                if hasattr(parent, 'updateRepeatedTasksList'):
                    parent.updateRepeatedTasksList()
                elif hasattr(parent, 'main_app') and hasattr(parent.main_app, 'updateRepeatedTasksList'):
                    parent.main_app.updateRepeatedTasksList()

        except Exception as e:
            print(f"Error checking scheduled tasks: {e}")

    @staticmethod
    def _createNewScheduledTask(original_task, current_date):
        """Buat task baru berdasarkan task asli dengan tanggal saat ini."""
        try:
            # Parse waktu asli
            original_start = datetime.strptime(
                original_task["start_time"], "%Y-%m-%d %H:%M"
            )
            original_deadline = datetime.strptime(
                original_task["deadline"], "%Y-%m-%d %H:%M"
            )

            # Hitung selisih waktu antara start dan deadline
            time_diff = original_deadline - original_start

            # Buat waktu start baru dengan tanggal hari ini
            new_start = datetime(
                current_date.year,
                current_date.month,
                current_date.day,
                original_start.hour,
                original_start.minute,
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
                "reminder": original_task.get("reminder", "None"),
                "status": "due",  # Status baru selalu "due"
                "schedule": original_task[
                    "schedule"
                ],  # Preserve the original schedule type
                "username": original_task["username"],
                "last_run_date": current_date.strftime(
                    "%Y-%m-%d"
                ),  # Tambahkan last_run_date
                "is_added": False,  # Tambahkan flag is_added
            }

            return new_task

        except (ValueError, TypeError) as e:
            print(f"Error creating new scheduled task: {e}")
            return None


class AddRepeatedTaskDialog(QDialog):
    """Dialog untuk add schedule task"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Repeated Task")
        self.setMinimumWidth(400)
        self.setup_ui()

    def update_text(self, key, new_text):
        """Update text when language changes"""
        if key == "add_repeated_task":
            self.setWindowTitle(new_text)
            self.ok_button.setText(new_text)
        elif key == "task_name":
            self.name_label.setText(new_text)
        elif key == "description":
            self.desc_label.setText(new_text)
        elif key == "start_time":
            self.time_label.setText(new_text)
        elif key == "repeat":
            self.schedule_label.setText(new_text)
        elif key == "select_days":
            self.weekly_day_label.setText(new_text)
        elif key == "select_dates":
            self.monthly_date_label.setText(new_text)
        elif key == "priority":
            self.priority_label.setText(new_text)
        elif key == "cancel":
            self.cancel_button.setText(new_text)

    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Task name
        name_layout = QVBoxLayout()
        self.name_label = QLabel("Task Name:")
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
        name_layout.addWidget(self.name_label)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Task description
        desc_layout = QVBoxLayout()
        self.desc_label = QLabel("Description:")
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
        desc_layout.addWidget(self.desc_label)
        desc_layout.addWidget(self.desc_edit)
        layout.addLayout(desc_layout)

        # Start time
        time_layout = QVBoxLayout()
        self.time_label = QLabel("Start Time:")
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
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.time_edit)
        layout.addLayout(time_layout)

        # Schedule type
        schedule_layout = QVBoxLayout()
        self.schedule_label = QLabel("Repeat:")
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
        schedule_layout.addWidget(self.schedule_label)
        schedule_layout.addWidget(self.schedule_combo)
        layout.addLayout(schedule_layout)

        # Day selection for weekly tasks
        self.weekly_container = QWidget()
        weekly_layout = QVBoxLayout(self.weekly_container)
        self.weekly_day_label = QLabel("Select Days:")
        self.weekly_day_label.setStyleSheet("font-size: 14px;")
        
        # Create a widget to hold checkboxes
        self.weekly_days_widget = QWidget()
        weekly_days_layout = QVBoxLayout(self.weekly_days_widget)
        weekly_days_layout.setSpacing(5)
        
        # Create checkboxes for each day
        self.weekly_checkboxes = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days:
            checkbox = QCheckBox(day)
            checkbox.setStyleSheet(
                """
                QCheckBox {
                    font-size: 14px;
                    padding: 5px;
                }
                QCheckBox:hover {
                    background-color: #E3F8FF;
                    border-radius: 4px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                }
                QCheckBox::indicator:unchecked {
                    border: 2px solid #ccc;
                    border-radius: 3px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #00B4D8;
                    border-radius: 3px;
                    background-color: #00B4D8;
                }
                """
            )
            self.weekly_checkboxes[day] = checkbox
            weekly_days_layout.addWidget(checkbox)
        
        weekly_layout.addWidget(self.weekly_day_label)
        weekly_layout.addWidget(self.weekly_days_widget)
        self.weekly_container.setVisible(False)
        layout.addWidget(self.weekly_container)

        # Date selection for monthly tasks
        self.monthly_container = QWidget()
        monthly_layout = QVBoxLayout(self.monthly_container)
        self.monthly_date_label = QLabel("Select Dates:")
        self.monthly_date_label.setStyleSheet("font-size: 14px;")
        
        # Create a widget to hold date buttons
        self.monthly_dates_widget = QWidget()
        monthly_dates_layout = QVBoxLayout(self.monthly_dates_widget)
        
        # Create a grid layout for date buttons
        self.monthly_dates_grid = QGridLayout()
        self.monthly_dates_grid.setSpacing(5)
        
        # Create buttons for each date
        self.monthly_date_buttons = {}
        for i in range(1, 32):
            btn = QPushButton(str(i))
            btn.setCheckable(True)
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: white;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #E3F8FF;
                    border: 1px solid #00B4D8;
                }
                QPushButton:checked {
                    background-color: #00B4D8;
                    color: white;
                    border: none;
                }
                """
            )
            row = (i - 1) // 7
            col = (i - 1) % 7
            self.monthly_dates_grid.addWidget(btn, row, col)
            self.monthly_date_buttons[i] = btn
        
        monthly_dates_layout.addLayout(self.monthly_dates_grid)
        monthly_layout.addWidget(self.monthly_date_label)
        monthly_layout.addWidget(self.monthly_dates_widget)
        self.monthly_container.setVisible(False)
        layout.addWidget(self.monthly_container)

        # Connect schedule type change
        self.schedule_combo.currentTextChanged.connect(self.on_schedule_type_changed)

        # Priority
        priority_layout = QVBoxLayout()
        self.priority_label = QLabel("Priority:")
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
        priority_layout.addWidget(self.priority_label)
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
        """Mengubah tampilan sesuai jadwal yang dipilih"""
        self.weekly_container.setVisible(schedule_type == "Weekly")
        self.monthly_container.setVisible(schedule_type == "Monthly")

    def get_task_data(self):
        """mengembalikan data task yang diinput"""
        schedule_type = self.schedule_combo.currentText().lower()
        schedule_data = schedule_type

        if schedule_type == "weekly":
            # Get all checked days
            selected_days = [day.lower() for day, checkbox in self.weekly_checkboxes.items() if checkbox.isChecked()]
            if not selected_days:
                QMessageBox.warning(self, "Warning", "Please select at least one day!")
                return None
            schedule_data = f"weekly_{','.join(selected_days)}"
        elif schedule_type == "monthly":
            # Get all checked dates
            selected_dates = [str(date) for date, btn in self.monthly_date_buttons.items() if btn.isChecked()]
            if not selected_dates:
                QMessageBox.warning(self, "Warning", "Please select at least one date!")
                return None
            schedule_data = f"monthly_{','.join(selected_dates)}"

        return {
            "name": self.name_edit.text(),
            "description": self.desc_edit.toPlainText(),
            "start_time": self.time_edit.time().toString("HH:mm"),
            "schedule": schedule_data,
            "priority": self.priority_combo.currentText(),
            "status": "due",
            "username": self.parent().main_app.current_user,
        }

    @staticmethod
    def addRepeatedTask(parent):
        """Add repeated task baru."""
        try:
            dialog = AddRepeatedTaskDialog(parent)
            if dialog.exec_():
                try:
                    task_data = dialog.get_task_data()

                    # Validate task data
                    if not task_data["name"]:
                        QMessageBox.warning(parent, "Error", "Task name is required.")
                        return

                    # Validate time format
                    try:
                        start_time = datetime.strptime(
                            task_data["start_time"], "%H:%M"
                        ).time()
                    except ValueError:
                        QMessageBox.warning(parent, "Error", "Invalid time format.")
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
                        "username": parent.main_app.current_user,
                        "last_run_date": start_datetime.strftime("%Y-%m-%d"),
                        "is_added": False,  # Flag to indicate if task is added
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
                                parent, "Error", f"Missing required field: {field}"
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

                    scheduled_tasks.append(task)

                    with open(schedule_file, "w", encoding="utf-8") as file:
                        json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

                    # Refresh the display
                    parent.updateRepeatedTasksList()
                    # QMessageBox.information(
                    #     parent, "Success", "Task has been added successfully."
                    # )

                except Exception as e:
                    QMessageBox.critical(
                        parent, "Error", f"Error processing task data: {str(e)}"
                    )

        except Exception as e:
            QMessageBox.critical(
                parent, "Error", f"Failed to create task dialog: {str(e)}"
            )
            print(f"Error in addRepeatedTask: {str(e)}")  # For debugging
