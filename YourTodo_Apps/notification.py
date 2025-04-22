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
from path_utils import get_image_path, get_database_path

class NotificationSystem:
    """
    System for managing and displaying notifications for tasks.
    Handles start time, deadline, and reminder notifications.
    """
    
    def __init__(self, main_app):
        self.main_app = main_app
        self.notifications = []
        self.notified_tasks = set()  # Track tasks that have already been notified
        self.notification_file = get_database_path("notifications.json")
        self.notified_tasks_file = get_database_path("notified_tasks.json")  # File to store notified tasks
        self.task_hashes_file = get_database_path("task_hashes.json")  # File to store task hashes
        self.task_hashes = {}  # Dictionary to store task hashes
        self.load_notifications()
        self.load_task_hashes()
        self.load_notified_tasks()
        
        # Set up system tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(QIcon(get_image_path("logo.png")))
        self.tray_icon.setVisible(True)
        
        # Create tray menu
        tray_menu = QMenu()
        show_action = QAction("Show Notifications", self.tray_icon)
        show_action.triggered.connect(self.show_notifications)
        tray_menu.addAction(show_action)
        self.tray_icon.setContextMenu(tray_menu)
        
        # Set up timer to check for notifications
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_notifications)
        self.timer.start(15000)  # Check every 15 sec
        
    def load_notifications(self):
        """Load saved notifications from file."""
        try:
            if os.path.exists(self.notification_file):
                with open(self.notification_file, 'r') as f:
                    self.notifications = json.load(f)
        except Exception as e:
            print(f"Error loading notifications: {e}")
            self.notifications = []
            
    def load_task_hashes(self):
        """Load saved task hashes from file."""
        try:
            if os.path.exists(self.task_hashes_file):
                with open(self.task_hashes_file, 'r') as f:
                    self.task_hashes = json.load(f)
        except Exception as e:
            print(f"Error loading task hashes: {e}")
            self.task_hashes = {}
            
    def load_notified_tasks(self):
        """Load saved notified tasks from file."""
        try:
            if os.path.exists(self.notified_tasks_file):
                with open(self.notified_tasks_file, 'r') as f:
                    self.notified_tasks = set(json.load(f))
        except Exception as e:
            print(f"Error loading notified tasks: {e}")
            self.notified_tasks = set()
            
    def save_notifications(self):
        """Save notifications to file."""
        try:
            with open(self.notification_file, 'w') as f:
                json.dump(self.notifications, f)
        except Exception as e:
            print(f"Error saving notifications: {e}")
            
    def save_task_hashes(self):
        """Save task hashes to file."""
        try:
            with open(self.task_hashes_file, 'w') as f:
                json.dump(self.task_hashes, f)
        except Exception as e:
            print(f"Error saving task hashes: {e}")
            
    def save_notified_tasks(self):
        """Save notified tasks to file."""
        try:
            with open(self.notified_tasks_file, 'w') as f:
                json.dump(list(self.notified_tasks), f)
        except Exception as e:
            print(f"Error saving notified tasks: {e}")
            
    def calculate_task_hash(self, task):
        """Calculate a hash for a task based on its properties."""
        # Create a string with all task properties
        task_str = f"{task['name']}_{task['description']}_{task['start_time']}_{task['deadline']}_{task['priority']}_{task['reminder']}_{task['status']}_{task['schedule']}"
        return hash(task_str)
            
    def add_notification(self, task_id, message, notification_type, timestamp=None):
        """Add a new notification."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        # Check if this notification already exists for this user
        for notification in self.notifications:
            if (notification.get("task_id") == task_id and 
                notification.get("type") == notification_type and
                notification.get("username") == self.main_app.current_user):
                # Notification already exists, don't add it again
                return
            
        notification = {
            "task_id": task_id,
            "message": message,
            "type": notification_type,
            "timestamp": timestamp,
            "read": False,
            "username": self.main_app.current_user
        }
        
        self.notifications.append(notification)
        self.save_notifications()
        
    def mark_as_read(self, notification_index):
        """Mark a notification as read."""
        if 0 <= notification_index < len(self.notifications):
            self.notifications[notification_index]["read"] = True
            self.save_notifications()
            
    def clear_notifications(self):
        """Clear all notifications for current user."""
        self.notifications = [n for n in self.notifications if n.get("username") != self.main_app.current_user]
        self.save_notifications()
        
    def check_notifications(self):
        """Check for new notifications based on task times."""
        if not self.main_app.current_user:
            return
            
        tasks_file = get_database_path("tasks.txt")
        try:
            # Load tasks from file
            tasks = []
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
                            tasks.append(task_dict)
            except FileNotFoundError:
                return
                
            current_time = datetime.now()
            
            for task in tasks:
                task_id = f"{task['name']}_{task['start_time']}_{task['deadline']}"
                
                # Calculate current hash for the task
                current_hash = self.calculate_task_hash(task)
                
                # Check if task has been modified
                task_modified = True
                if task_id in self.task_hashes:
                    if self.task_hashes[task_id] == current_hash:
                        task_modified = False
                
                # Update task hash
                self.task_hashes[task_id] = current_hash
                self.save_task_hashes()
                
                # Skip if task is already done or failed
                if task['status'].lower() in ['done', 'failed']:
                    continue
                    
                # Check start time notification
                if task['start_time'] != "None" and task['start_time'] != "":
                    start_time = datetime.strptime(task['start_time'], "%Y-%m-%d %H:%M")
                    start_notification_id = f"{task_id}_start"
                    
                    # If start time has just arrived (within last minute) and task has been modified
                    if (current_time >= start_time and 
                        current_time - start_time <= timedelta(minutes=1) and
                        (start_notification_id not in self.notified_tasks or task_modified)):
                        self.add_notification(
                            task_id, 
                            f"Task '{task['name']}' has started!", 
                            "start_time"
                        )
                        self.notified_tasks.add(start_notification_id)
                        self.save_notified_tasks()
                        self.tray_icon.showMessage(
                            "Task Started", 
                            f"Task '{task['name']}' has started!", 
                            QSystemTrayIcon.Information, 
                            5000
                        )
                
                # Check deadline notification
                if task['deadline'] != "None" and task['deadline'] != "":
                    deadline = datetime.strptime(task['deadline'], "%Y-%m-%d %H:%M")
                    deadline_notification_id = f"{task_id}_deadline"
                    
                    # If deadline has just arrived (within last minute) and task has been modified
                    if (current_time >= deadline and 
                        current_time - deadline <= timedelta(minutes=1) and
                        (deadline_notification_id not in self.notified_tasks or task_modified)):
                        self.add_notification(
                            task_id, 
                            f"Task '{task['name']}' deadline has arrived!", 
                            "deadline"
                        )
                        self.notified_tasks.add(deadline_notification_id)
                        self.save_notified_tasks()
                        self.tray_icon.showMessage(
                            "Deadline Arrived", 
                            f"Task '{task['name']}' deadline has arrived!", 
                            QSystemTrayIcon.Warning, 
                            5000
                        )
                    
                    # Check if deadline has passed and task has been modified
                    if (current_time > deadline and 
                        current_time - deadline <= timedelta(minutes=1) and
                        (f"{task_id}_failed" not in self.notified_tasks or task_modified)):
                        self.add_notification(
                            task_id, 
                            f"Task '{task['name']}' has failed (deadline passed)!", 
                            "failed"
                        )
                        self.notified_tasks.add(f"{task_id}_failed")
                        self.save_notified_tasks()
                        self.tray_icon.showMessage(
                            "Task Failed", 
                            f"Task '{task['name']}' has failed (deadline passed)!", 
                            QSystemTrayIcon.Critical, 
                            5000
                        )
                
                # Check reminder notifications
                reminder = task.get('reminder', 'None')
                if reminder != "None" and reminder != "":
                    try:
                        # Parse reminder time and type, handling both formats:
                        # "5 minutes before" and "5 before"
                        parts = reminder.lower().split()
                        if len(parts) >= 2:
                            reminder_minutes = int(parts[0])
                            reminder_type = parts[-1]  # Get the last word which should be "before"
                            
                            if reminder_type == "before":
                                # Check start time reminder
                                if task['start_time'] != "None" and task['start_time'] != "":
                                    start_time = datetime.strptime(task['start_time'], "%Y-%m-%d %H:%M")
                                    reminder_time = start_time - timedelta(minutes=reminder_minutes)
                                    reminder_id = f"{task_id}_start_reminder"
                                    
                                    # Check if we're within the reminder window
                                    time_diff = start_time - current_time
                                    if (time_diff.total_seconds() > 0 and  # Task hasn't started yet
                                        time_diff.total_seconds() <= reminder_minutes * 60 and  # Within reminder window
                                        (reminder_id not in self.notified_tasks or task_modified)):
                                        self.add_notification(
                                            task_id,
                                            f"Task '{task['name']}' starts in {reminder_minutes} minutes!",
                                            "reminder"
                                        )
                                        self.notified_tasks.add(reminder_id)
                                        self.save_notified_tasks()
                                        self.tray_icon.showMessage(
                                            "Task Reminder",
                                            f"Task '{task['name']}' starts in {reminder_minutes} minutes!",
                                            QSystemTrayIcon.Information,
                                            5000
                                        )
                                
                                # Check deadline reminder
                                if task['deadline'] != "None" and task['deadline'] != "":
                                    deadline = datetime.strptime(task['deadline'], "%Y-%m-%d %H:%M")
                                    reminder_time = deadline - timedelta(minutes=reminder_minutes)
                                    reminder_id = f"{task_id}_deadline_reminder"
                                    
                                    # Check if we're within the reminder window
                                    time_diff = deadline - current_time
                                    if (time_diff.total_seconds() > 0 and  # Deadline hasn't passed yet
                                        time_diff.total_seconds() <= reminder_minutes * 60 and  # Within reminder window
                                        (reminder_id not in self.notified_tasks or task_modified)):
                                        self.add_notification(
                                            task_id,
                                            f"Task '{task['name']}' deadline is in {reminder_minutes} minutes!",
                                            "reminder"
                                        )
                                        self.notified_tasks.add(reminder_id)
                                        self.save_notified_tasks()
                                        self.tray_icon.showMessage(
                                            "Deadline Reminder",
                                            f"Task '{task['name']}' deadline is in {reminder_minutes} minutes!",
                                            QSystemTrayIcon.Warning,
                                            5000
                                        )
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing reminder '{reminder}': {e}")
                        continue
                
                # Check for task completion notification
                if task['status'].lower() == 'done' and (f"{task_id}_done" not in self.notified_tasks or task_modified):
                    self.add_notification(
                        task_id, 
                        f"Task '{task['name']}' has been completed!", 
                        "done"
                    )
                    self.notified_tasks.add(f"{task_id}_done")
                    self.save_notified_tasks()
                    self.tray_icon.showMessage(
                        "Task Completed", 
                        f"Task '{task['name']}' has been completed!", 
                        QSystemTrayIcon.Information, 
                        5000
                    )
                    
        except Exception as e:
            print(f"Error checking notifications: {e}")
            
    def show_notifications(self):
        """Show the notifications widget."""
        if hasattr(self.main_app, 'notification_widget'):
            self.main_app.notification_widget.loadNotifications()
            self.main_app.notification_widget.show()


class NotificationWidget(QWidget):
    """
    Widget that displays notifications for tasks.
    Shows upcoming deadlines, task updates, and other notifications.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.notification_system = None
        if parent and hasattr(parent, 'notification_system'):
            self.notification_system = parent.notification_system
        self.refresh_animation = None
        self.initUI()

    def initUI(self):
        """Initialize the notification widget UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QHBoxLayout()
        title = QLabel("Notifications")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #333;")
        header.addWidget(title)
        header.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet("""
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
        """)
        self.refresh_btn.clicked.connect(self.refresh_notifications)
        header.addWidget(self.refresh_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet("""
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
        """)
        clear_btn.clicked.connect(self.clear_notifications)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)

        # Notifications list
        self.notifications_list = QListWidget()
        self.notifications_list.setStyleSheet("""
            QListWidget {
                background: white;
                border-radius: 8px;
                padding: 8px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """)
        layout.addWidget(self.notifications_list)

        self.setLayout(layout)
        self.refresh_notifications()
        
    def start_refresh_animation(self):
        """Start the refresh button rotation animation."""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Refreshing...")
        
        # Create rotation animation
        self.refresh_animation = QPropertyAnimation(self.refresh_btn, b"rotation")
        self.refresh_animation.setDuration(1000)  # 1 second per rotation
        self.refresh_animation.setStartValue(0)
        self.refresh_animation.setEndValue(360)
        self.refresh_animation.setLoopCount(-1)  # Infinite loop
        self.refresh_animation.setEasingCurve(QEasingCurve.Linear)
        self.refresh_animation.start()

    def stop_refresh_animation(self):
        """Stop the refresh button rotation animation."""
        if self.refresh_animation:
            self.refresh_animation.stop()
            self.refresh_animation = None
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Refresh")
        
    def refresh_notifications(self):
        """Refresh the notifications list with animation."""
        # Start refresh animation
        self.start_refresh_animation()
        
        # Use QTimer to simulate async operation
        QTimer.singleShot(1000, self._do_refresh)
        
    def _do_refresh(self):
        """Perform the actual refresh operation."""
        # Check for new notifications
        if self.notification_system:
            self.notification_system.check_notifications()
        
        # Reload the notifications display
        self.loadNotifications()
        
        # Stop refresh animation
        self.stop_refresh_animation()
        
    def loadNotifications(self):
        """Load and display notifications."""
        self.notifications_list.clear() 
        
        if not self.notification_system or not self.main_app.current_user:
            return
            
        # Filter notifications for current user and sort by timestamp (newest first)
        user_notifications = [
            n for n in self.notification_system.notifications 
            if n.get("username") == self.main_app.current_user
        ]
        
        # Remove duplicates based on task_id and type
        unique_notifications = []
        seen = set()
        for notification in user_notifications:
            key = (notification.get("task_id"), notification.get("type"))
            if key not in seen:
                seen.add(key)
                unique_notifications.append(notification)
        
        sorted_notifications = sorted(
            unique_notifications, 
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        
        for notification in sorted_notifications:
            item = QListWidgetItem()
            
            # Create notification widget
            notification_widget = QWidget()
            notification_layout = QVBoxLayout(notification_widget)
            
            # Message
            message_label = QLabel(notification["message"])
            message_label.setFont(QFont("Arial", 12))
            message_label.setWordWrap(True)
            
            # Timestamp
            timestamp = datetime.strptime(notification["timestamp"], "%Y-%m-%d %H:%M:%S")
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")
            time_label = QLabel(formatted_time)
            time_label.setStyleSheet("color: #666; font-size: 10px;")
            
            # Type indicator
            type_label = QLabel(notification["type"].replace("_", " ").title())
            type_label.setStyleSheet(
                f"""
                color: white;
                background-color: {self._get_type_color(notification["type"])};
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 10px;
                """
            )
            
            # Add widgets to layout
            notification_layout.addWidget(message_label)
            
            # Bottom row with time and type
            bottom_row = QHBoxLayout()
            bottom_row.addWidget(time_label)
            bottom_row.addStretch()
            bottom_row.addWidget(type_label)
            notification_layout.addLayout(bottom_row)
            
            # Set item widget
            item.setSizeHint(notification_widget.sizeHint())
            self.notifications_list.addItem(item)
            self.notifications_list.setItemWidget(item, notification_widget)
            
    def _get_type_color(self, notification_type):
        """Get color for notification type."""
        colors = {
            "start_time": "#4CAF50",  # Green
            "deadline": "#FF9800",    # Orange
            "start_reminder": "#2196F3",  # Blue
            "deadline_reminder": "#FF5722",  # Deep Orange
            "failed": "#F44336",      # Red
            "done": "#4CAF50"         # Green
        }
        return colors.get(notification_type, "#9E9E9E")  # Default gray
        
    def clear_notifications(self):
        """Clear all notifications."""
        if self.notification_system:
            self.notification_system.clear_notifications()
            self.refresh_notifications() 