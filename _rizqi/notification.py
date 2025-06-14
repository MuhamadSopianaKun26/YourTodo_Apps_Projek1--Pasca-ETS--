from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSystemTrayIcon,
    QMenu,
    QAction,
    QPushButton,
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QDateTime, QTimer, QPropertyAnimation, QEasingCurve, QPoint
import os
import json
from datetime import datetime, timedelta
from _sopian.path_utils import get_image_path, get_database_path


class NotificationSystem:
    """
    Sistem untuk mengelola dan menampilkan notifikasi untuk tugas.
    Menangani notifikasi waktu mulai, tenggat waktu, dan pengingat.
    """

    def __init__(self, main_app):
        self.main_app = main_app
        self.notifications = []
        self.notified_tasks = set()  # Melacak tugas yang sudah diberi notifikasi
        self.notification_file = get_database_path("notifications.json")
        self.notified_tasks_file = get_database_path("notified_tasks.json")
        self.task_hashes_file = get_database_path("task_hashes.json")
        self.task_hashes = {}

        # Pastikan direktori ada
        os.makedirs(os.path.dirname(self.notification_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.notified_tasks_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.task_hashes_file), exist_ok=True)

        self.load_notifications()
        self.load_task_hashes()
        self.load_notified_tasks()

        # Siapkan ikon baki sistem
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(QIcon(get_image_path("logo.png")))
        self.tray_icon.setVisible(True)

        # Buat menu baki
        tray_menu = QMenu()
        show_action = QAction("Show Notifications", self.tray_icon)
        show_action.triggered.connect(self.show_notifications)
        tray_menu.addAction(show_action)
        self.tray_icon.setContextMenu(tray_menu)

        # Siapkan timer untuk memeriksa notifikasi
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_notifications)
        self.timer.start(15000)  # Periksa setiap 15 detik

    def load_notifications(self):
        """Muat notifikasi yang disimpan dari file."""
        try:
            if os.path.exists(self.notification_file):
                with open(self.notification_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.notifications = data
                    else:
                        self.notifications = []
            else:
                self.notifications = []
                self.save_notifications()
        except Exception as e:
            print(f"Error loading notifications: {e}")
            self.notifications = []
            self.save_notifications()

    def load_task_hashes(self):
        """Muat hash tugas yang disimpan dari file."""
        try:
            if os.path.exists(self.task_hashes_file):
                with open(self.task_hashes_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.task_hashes = data
                    else:
                        self.task_hashes = {}
        except Exception as e:
            print(f"Error loading task hashes: {e}")
            self.task_hashes = {}

    def load_notified_tasks(self):
        """Muat tugas yang sudah diberi notifikasi dari file."""
        try:
            if os.path.exists(self.notified_tasks_file):
                with open(self.notified_tasks_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.notified_tasks = set(data)
                    else:
                        self.notified_tasks = set()
        except Exception as e:
            print(f"Error loading notified tasks: {e}")
            self.notified_tasks = set()

    def save_notifications(self):
        """Simpan notifikasi ke file."""
        try:
            with open(self.notification_file, "w") as f:
                json.dump(self.notifications, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving notifications: {e}")

    def save_task_hashes(self):
        """Simpan hash tugas ke file."""
        try:
            with open(self.task_hashes_file, "w") as f:
                json.dump(self.task_hashes, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving task hashes: {e}")

    def save_notified_tasks(self):
        """Simpan tugas yang sudah diberi notifikasi ke file."""
        try:
            with open(self.notified_tasks_file, "w") as f:
                json.dump(list(self.notified_tasks), f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving notified tasks: {e}")

    def calculate_task_hash(self, task):
        """Hitung hash untuk tugas berdasarkan propertinya."""
        task_str = f"{task['name']}_{task['description']}_{task['start_time']}_{task['deadline']}_{task['priority']}_{task['reminder']}_{task['status']}_{task['schedule']}"
        return hash(task_str)

    def add_notification(self, task_id, message, notification_type, timestamp=None):
        """Tambahkan notifikasi baru."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Periksa duplikasi notifikasi
        for notification in self.notifications:
            if (
                notification.get("task_id") == task_id
                and notification.get("type") == notification_type
                and notification.get("username") == self.main_app.current_user
            ):
                return

        notification = {
            "task_id": task_id,
            "message": message,
            "type": notification_type,
            "timestamp": timestamp,
            "read": False,
            "username": self.main_app.current_user,
        }

        self.notifications.append(notification)
        self.save_notifications()

    def mark_as_read(self, notification_index):
        """Tandai notifikasi sebagai sudah dibaca."""
        if 0 <= notification_index < len(self.notifications):
            self.notifications[notification_index]["read"] = True
            self.save_notifications()

    def clear_notifications(self):
        """Hapus semua notifikasi untuk pengguna saat ini."""
        self.notifications = [
            n
            for n in self.notifications
            if n.get("username") != self.main_app.current_user
        ]
        self.save_notifications()

    def check_notifications(self):
        """Periksa notifikasi baru berdasarkan waktu tugas."""
        if not self.main_app.current_user:
            return

        task_file = get_database_path("tasks.json")
        try:
            # Muat tugas dari file
            tasks = []
            try:
                with open(task_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    for task in data.get("tasks", []):
                        if task.get("username") == self.main_app.current_user:
                            tasks.append(task)
            except FileNotFoundError:
                return
            except json.JSONDecodeError:
                print("Error: Invalid JSON format in tasks file")
                return

            current_time = datetime.now()

            for task in tasks:
                task_id = f"{task['name']}_{task['start_time']}_{task['deadline']}"
                current_hash = self.calculate_task_hash(task)

                # Periksa apakah tugas telah dimodifikasi
                task_modified = True
                if task_id in self.task_hashes:
                    if self.task_hashes[task_id] == current_hash:
                        task_modified = False

                # Perbarui hash tugas
                self.task_hashes[task_id] = current_hash
                self.save_task_hashes()

                # Lewati jika tugas sudah selesai atau gagal
                if task.get("status", "").lower() in ["done", "failed"]:
                    continue

                # Periksa notifikasi waktu mulai
                if task.get("start_time") not in ["None", "", None]:
                    try:
                        start_time = datetime.strptime(
                            task["start_time"], "%Y-%m-%d %H:%M"
                        )
                        start_notification_id = f"{task_id}_start"

                        if (
                            current_time >= start_time
                            and current_time - start_time <= timedelta(minutes=1)
                            and (
                                start_notification_id not in self.notified_tasks
                                or task_modified
                            )
                        ):
                            self.add_notification(
                                task_id,
                                f"Task '{task['name']}' has started!",
                                "start_time",
                            )
                            self.notified_tasks.add(start_notification_id)
                            self.save_notified_tasks()
                            self.tray_icon.showMessage(
                                "Task Started",
                                f"Task '{task['name']}' has started!",
                                QSystemTrayIcon.Information,
                                5000,
                            )
                    except ValueError as e:
                        print(f"Error parsing start time: {e}")

                # Periksa notifikasi tenggat waktu
                if task.get("deadline") not in ["None", "", None]:
                    try:
                        deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
                        deadline_notification_id = f"{task_id}_deadline"

                        if (
                            current_time >= deadline
                            and current_time - deadline <= timedelta(minutes=1)
                            and (
                                deadline_notification_id not in self.notified_tasks
                                or task_modified
                            )
                        ):
                            self.add_notification(
                                task_id,
                                f"Task '{task['name']}' deadline has arrived!",
                                "deadline",
                            )
                            self.notified_tasks.add(deadline_notification_id)
                            self.save_notified_tasks()
                            self.tray_icon.showMessage(
                                "Deadline Arrived",
                                f"Task '{task['name']}' deadline has arrived!",
                                QSystemTrayIcon.Warning,
                                5000,
                            )

                        # Periksa jika tenggat waktu telah berlalu
                        if (
                            current_time > deadline
                            and current_time - deadline <= timedelta(minutes=1)
                            and (
                                f"{task_id}_failed" not in self.notified_tasks
                                or task_modified
                            )
                        ):
                            self.add_notification(
                                task_id,
                                f"Task '{task['name']}' has failed (deadline exceeded)!",
                                "failed",
                            )
                            self.notified_tasks.add(f"{task_id}_failed")
                            self.save_notified_tasks()
                            self.tray_icon.showMessage(
                                "Task Failed",
                                f"Task '{task['name']}' has failed (deadline exceeded)!",
                                QSystemTrayIcon.Critical,
                                5000,
                            )
                    except ValueError as e:
                        print(f"Error parsing deadline: {e}")

                # Periksa notifikasi pengingat
                reminder = task.get("reminder", "None")
                if reminder not in ["None", "", None]:
                    try:
                        parts = reminder.lower().split()
                        if len(parts) >= 2:
                            reminder_minutes = int(parts[0])
                            reminder_type = parts[-1]
                            
                            # Buat objek timedelta langsung dari reminder_minutes
                            reminder_duration = timedelta(minutes=reminder_minutes)

                            if reminder_type == "before":
                                # Periksa pengingat waktu mulai
                                if task.get("start_time") not in ["None", "", None]:
                                    try:
                                        start_time = datetime.strptime(
                                            task["start_time"], "%Y-%m-%d %H:%M"
                                        )
                                        reminder_id = f"{task_id}_start_reminder"

                                        time_diff = start_time - current_time
                                        if (
                                            time_diff > timedelta(seconds=0) # Pastikan time_diff positif
                                            and time_diff <= reminder_duration
                                            and (
                                                reminder_id not in self.notified_tasks
                                                or task_modified
                                            )
                                        ):
                                            self.add_notification(
                                                task_id,
                                                f"Task '{task['name']}' starts in {reminder_minutes} minutes!",
                                                "reminder",
                                            )
                                            self.notified_tasks.add(reminder_id)
                                            self.save_notified_tasks()
                                            self.tray_icon.showMessage(
                                                "Task Reminder",
                                                f"Task '{task['name']}' starts in {reminder_minutes} minutes!",
                                                QSystemTrayIcon.Information,
                                                5000,
                                            )
                                    except ValueError as e:
                                        print(
                                            f"Error parsing start time for reminder: {e}"
                                        )

                                # Periksa pengingat tenggat waktu
                                if task.get("deadline") not in ["None", "", None]:
                                    try:
                                        deadline = datetime.strptime(
                                            task["deadline"], "%Y-%m-%d %H:%M"
                                        )
                                        reminder_id = f"{task_id}_deadline_reminder"

                                        time_diff = deadline - current_time
                                        if (
                                            time_diff > timedelta(seconds=0) # Pastikan time_diff positif
                                            and time_diff <= reminder_duration
                                            and (
                                                reminder_id not in self.notified_tasks
                                                or task_modified
                                            )
                                        ):
                                            self.add_notification(
                                                task_id,
                                                f"Task '{task['name']}' deadline in {reminder_minutes} minutes!",
                                                "reminder",
                                            )
                                            self.notified_tasks.add(reminder_id)
                                            self.save_notified_tasks()
                                            self.tray_icon.showMessage(
                                                "Deadline Reminder",
                                                f"Task '{task['name']}' deadline in {reminder_minutes} minutes!",
                                                QSystemTrayIcon.Warning,
                                                5000,
                                            )
                                    except ValueError as e:
                                        print(
                                            f"Error parsing deadline for reminder: {e}"
                                        )
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing reminder '{reminder}': {e}")

                # Periksa notifikasi penyelesaian tugas
                if task.get("status", "").lower() == "done" and (
                    f"{task_id}_done" not in self.notified_tasks or task_modified
                ):
                    self.add_notification(
                        task_id, f"Task '{task['name']}' has been completed!", "done"
                    )
                    self.notified_tasks.add(f"{task_id}_done")
                    self.save_notified_tasks()
                    self.tray_icon.showMessage(
                        "Task Completed",
                        f"Task '{task['name']}' has been completed!",
                        QSystemTrayIcon.Information,
                        5000,
                    )

        except Exception as e:
            print(f"Error checking notifications: {e}")

    def show_notifications(self):
        """Tampilkan widget notifikasi."""
        if hasattr(self.main_app, "notification_widget"):
            self.main_app.notification_widget.loadNotifications()
            self.main_app.showSection("notifications")


class NotificationWidget(QWidget):
    """
    Widget yang menampilkan notifikasi untuk tugas.
    Menampilkan tenggat waktu mendatang, pembaruan tugas, dan notifikasi lainnya.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.notification_system = (
            parent.notification_system
            if parent and hasattr(parent, "notification_system")
            else None
        )
        self.refresh_animation = None
        self.initUI()

    def initUI(self):
        """Inisialisasi komponen UI widget notifikasi."""
        self.setStyleSheet("background-color: #F5F5F5;")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Header
        header = QHBoxLayout()
        self.title = QLabel("Notifications")
        self.title.setFont(QFont("Arial", 18, QFont.Bold))
        self.title.setStyleSheet("color: #333;")
        header.addWidget(self.title)
        header.addStretch()

        # Tombol Refresh
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """
        )
        self.refresh_btn.clicked.connect(self.refresh_notifications)
        header.addWidget(self.refresh_btn)

        # Tombol Hapus
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """
        )
        self.clear_btn.clicked.connect(self.clear_notifications)
        header.addWidget(self.clear_btn)

        layout.addLayout(header)

        # Daftar Notifikasi
        self.notifications_list = QListWidget()
        self.notifications_list.setStyleSheet(
            """
            QListWidget {
                background: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
            QListWidget::item {
                border-bottom: 1px solid #E0E0E0;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """
        )
        self.notifications_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        layout.addWidget(self.notifications_list)

        self.setLayout(layout)
        self.loadNotifications()

    def start_refresh_animation(self):
        """Mulai animasi rotasi tombol refresh."""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Refreshing...")

        self.refresh_animation = QPropertyAnimation(self.refresh_btn, b"rotation")
        self.refresh_animation.setDuration(1000)
        self.refresh_animation.setStartValue(0)
        self.refresh_animation.setEndValue(360)
        self.refresh_animation.setLoopCount(-1)
        self.refresh_animation.setEasingCurve(QEasingCurve.Linear)
        self.refresh_animation.start()

    def stop_refresh_animation(self):
        """Hentikan animasi rotasi tombol refresh."""
        if self.refresh_animation:
            self.refresh_animation.stop()
            self.refresh_animation = None
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Refresh")

    def refresh_notifications(self):
        """Segarkan daftar notifikasi dengan animasi."""
        self.start_refresh_animation()
        QTimer.singleShot(1000, self._do_refresh)

    def _do_refresh(self):
        """Lakukan operasi penyegaran yang sebenarnya."""
        if self.notification_system:
            self.notification_system.check_notifications()
        self.loadNotifications()
        self.stop_refresh_animation()

    def loadNotifications(self):
        """Muat dan tampilkan notifikasi dengan pemformatan yang lebih baik."""
        self.notifications_list.clear()

        if not self.notification_system or not self.main_app.current_user:
            return

        # Saring dan urutkan notifikasi
        user_notifications = [
            n
            for n in self.notification_system.notifications
            if n.get("username") == self.main_app.current_user
        ]

        # Hapus duplikasi
        unique_notifications = []
        seen = set()
        for notification in user_notifications:
            key = (notification.get("task_id"), notification.get("type"))
            if key not in seen:
                seen.add(key)
                unique_notifications.append(notification)

        # Urutkan berdasarkan timestamp (terbaru lebih dulu)
        sorted_notifications = sorted(
            unique_notifications, key=lambda x: x["timestamp"], reverse=True
        )

        for notification in sorted_notifications:
            item = QListWidgetItem()
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)

            # Buat wadah notifikasi
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(15, 15, 15, 15)
            container_layout.setSpacing(8)

            # Label pesan
            message_label = QLabel(notification["message"])
            message_label.setWordWrap(True)
            message_label.setStyleSheet("font-size: 14px; color: #333;")

            # Baris bawah dengan waktu dan tipe
            bottom_row = QWidget()
            bottom_layout = QHBoxLayout(bottom_row)
            bottom_layout.setContentsMargins(0, 0, 0, 0)

            # Timestamp
            try:
                timestamp = datetime.strptime(
                    notification["timestamp"], "%Y-%m-%d %H:%M:%S"
                )
                time_label = QLabel(timestamp.strftime("%d %b, %H:%M"))
            except ValueError:
                time_label = QLabel(notification["timestamp"])
            time_label.setStyleSheet("color: #757575; font-size: 12px;")

            # Badge tipe
            type_display_name = notification["type"].replace("_", " ").title()
            if notification["type"] == "start_time":
                type_display_name = "Start Time"
            elif notification["type"] == "deadline":
                type_display_name = "Deadline"
            elif notification["type"] == "reminder":
                type_display_name = "Reminder"
            elif notification["type"] == "failed":
                type_display_name = "Failed"
            elif notification["type"] == "done":
                type_display_name = "Completed"

            type_label = QLabel(type_display_name)
            type_label.setStyleSheet(
                f"""
                color: white;
                background-color: {self._get_type_color(notification["type"])};
                border-radius: 10px;
                padding: 2px 10px;
                font-size: 11px;
                """
            )

            # Tambahkan widget ke layout
            container_layout.addWidget(message_label)
            bottom_layout.addWidget(time_label)
            bottom_layout.addStretch()
            bottom_layout.addWidget(type_label)
            container_layout.addWidget(bottom_row)

            # Atur widget item
            item.setSizeHint(container.sizeHint())
            self.notifications_list.addItem(item)
            self.notifications_list.setItemWidget(item, container)

    def _get_type_color(self, notification_type):
        """Dapatkan warna untuk tipe notifikasi."""
        colors = {
            "start_time": "#4CAF50",  # Hijau
            "deadline": "#FF9800",  # Oranye
            "reminder": "#2196F3",  # Biru
            "failed": "#F44336",  # Merah
            "done": "#4CAF50",  # Hijau
        }
        return colors.get(notification_type, "#9E9E9E")  # Abu-abu default

    def clear_notifications(self):
        """Hapus semua notifikasi."""
        if self.notification_system:
            self.notification_system.clear_notifications()
            self.loadNotifications()

    def update_text(self, key, new_text):
        """Perbarui teks saat bahasa berubah"""
        if key == "notifications":
            self.title.setText(new_text)
        elif key == "refresh":
            self.refresh_btn.setText(new_text)
        elif key == "clear_all":
            self.clear_btn.setText(new_text)
        # Muat ulang notifikasi untuk memperbarui teks yang diterjemahkan
        self.loadNotifications()