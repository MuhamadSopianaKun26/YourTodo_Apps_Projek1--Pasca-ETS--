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

        # Buat layout utama
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        # Sisi kiri - Info tugas
        info_layout = QVBoxLayout()
        name_label = QLabel(task_dict["name"])
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        desc_label = QLabel(task_dict.get("description", ""))
        desc_label.setStyleSheet("color: #666;")
        
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
            action = QAction(QIcon(icon_path), text, parent)
            action.triggered.connect(lambda checked, t=task_dict: RepeatedTaskManager.deleteScheduledTask(parent, t))
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
                parent,
                "Success",
                "Scheduled task has been deleted successfully!"
            )

            # Perbarui tampilan
            parent.refreshSchedule()

        except Exception as e:
            QMessageBox.critical(
                parent,
                "Error",
                f"Failed to delete scheduled task: {str(e)}"
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

            # Tambahkan tugas baru
            data["tasks"].append(task)

            # Simpan tugas yang diperbarui
            with open(tasks_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)

        except Exception as e:
            print(f"Error adding task to file: {e}")

    @staticmethod
    def checkAndAddScheduledTasks(parent):
        """Memeriksa dan menambahkan tugas berdasarkan jadwal."""
        tasks_file = get_database_path("tasks.json")
        schedule_file = get_database_path("scheduled_tasks.json")

        if (
            not parent.main_app
            or not hasattr(parent.main_app, "current_user")
            or not parent.main_app.current_user
        ):
            return

        current_date = datetime.now()
        current_day = current_date.day
        current_weekday = current_date.weekday()  # 0 = Monday, 6 = Sunday

        try:
            # Baca tugas yang dijadwalkan
            with open(schedule_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                scheduled_tasks = data.get("scheduled_tasks", [])

            # Proses setiap tugas yang dijadwalkan
            for task in scheduled_tasks:
                if task["username"] != parent.main_app.current_user:
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
                    # Buat instance tugas baru
                    new_task = task.copy()
                    new_task["start_time"] = current_date.strftime("%Y-%m-%d %H:%M")
                    new_task["status"] = "due"

                    # Tambahkan ke tasks.json
                    try:
                        with open(tasks_file, "r", encoding="utf-8") as file:
                            tasks_data = json.load(file)
                    except (FileNotFoundError, json.JSONDecodeError):
                        tasks_data = {"tasks": []}

                    tasks_data["tasks"].append(new_task)

                    with open(tasks_file, "w", encoding="utf-8") as file:
                        json.dump(tasks_data, file, indent=2)

                    # Update tanggal terakhir dijalankan
                    task["last_run_date"] = current_date.strftime("%Y-%m-%d")

            # Simpan tugas yang dijadwalkan yang diperbarui
            with open(schedule_file, "w", encoding="utf-8") as file:
                json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

            # Perbarui tampilan
            parent.loadScheduledTasks()

        except Exception as e:
            print(f"Error checking scheduled tasks: {e}")

    @staticmethod
    def _updateTaskStatusInFile(task_dict):
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

class AddRepeatedTaskDialog(QDialog):
    """Dialog untuk add schedule task"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Repeated Task")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        """Initialize dialog UI."""
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
        """Mengubah tampilan sesuai jadwal yang dipilih"""
        self.weekly_container.setVisible(schedule_type == "Weekly")
        self.monthly_container.setVisible(schedule_type == "Monthly")

    def get_task_data(self):
        """mengembalikan data task yang diinput"""
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

                    task["is_active"] = True
                    task["last_run_date"] = task["start_time"].split()[0]
                    scheduled_tasks.append(task)

                    with open(schedule_file, "w", encoding="utf-8") as file:
                        json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

                    # Refresh the display
                    parent.updateRepeatedTasksList()
                    QMessageBox.information(
                        parent, "Success", "Task has been added successfully."
                    )

                except Exception as e:
                    QMessageBox.critical(
                        parent, "Error", f"Error processing task data: {str(e)}"
                    )

        except Exception as e:
            QMessageBox.critical(
                parent, "Error", f"Failed to create task dialog: {str(e)}"
            )
            print(f"Error in addRepeatedTask: {str(e)}")  # For debugging 