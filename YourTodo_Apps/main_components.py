from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QFrame,
    QMenu,
    QAction,
    QMessageBox,
    QListWidget,
    QCalendarWidget,
    QListWidgetItem,
)
from PyQt5.QtCore import Qt, QSize, QDateTime
from PyQt5.QtGui import QIcon, QFont, QPixmap, QMovie
from path_utils import get_image_path


class HeaderWidget(QWidget):
    """
    A widget that represents the application header.
    Contains the application logo, search functionality, notifications,
    and user management components.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.username_label = None
        self.initUI()

    def initUI(self):
        """Initialize the header UI components and layout."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 10, 0)
        layout.setSpacing(0)

        layout.addWidget(self._createLogoContainer())
        layout.addWidget(self._createMainContainer())

        self.setLayout(layout)
        self.setStyleSheet("QWidget { background-color: white; }")

    def _createLogoContainer(self):
        """Create and return the logo container widget."""
        container = QWidget()
        container.setFixedWidth(200)
        container.setFixedHeight(100)
        container.setStyleSheet("background-color: white;")

        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)

        logo_label = QLabel()
        logo_pixmap = QPixmap(get_image_path("logo.png"))
        if not logo_pixmap.isNull():
            scaled_pixmap = logo_pixmap.scaled(
                200, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setFixedSize(scaled_pixmap.size())
        else:
            logo_label.setText("YourTodo")
            logo_label.setFont(QFont("Arial", 24, QFont.Bold))
            logo_label.setStyleSheet("color: #00B4D8;")

        layout.addWidget(logo_label, 0, Qt.AlignCenter)
        return container

    def _createMainContainer(self):
        """Create and return the main container with search, notifications, and user info."""
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 0, 0, 0)

        search_bar = self._createSearchBar()
        notif_btn = self._createNotificationButton()
        user_container = self._createUserContainer()

        layout.addWidget(search_bar)
        layout.addStretch()
        layout.addWidget(notif_btn)
        layout.addWidget(user_container)

        return container

    def _createSearchBar(self):
        """Create and return the search bar widget."""
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search tasks...")
        search_bar.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 15px;
                padding: 5px 15px;
                background: white;
                min-width: 300px;
                height: 30px;
            }
        """
        )
        return search_bar

    def _createNotificationButton(self):
        """Create and return the notification button widget."""
        notif_btn = QPushButton()
        notif_btn.setIcon(QIcon(get_image_path("notification.png")))
        notif_btn.setIconSize(QSize(24, 24))
        notif_btn.setFixedSize(40, 40)
        notif_btn.setStyleSheet(
            """
            QPushButton {
                border: none;
                border-radius: 20px;
                padding: 8px;
                background-color: transparent;
                margin: 0px 5px;
            }
            QPushButton:hover {
                background-color: #E3F8FF;
            }
        """
        )
        # Connect the notification button to show notification page
        if self.main_window:
            notif_btn.clicked.connect(lambda: self.main_window.showSection("notifications"))
            # Also update sidebar button state
            notif_btn.clicked.connect(lambda: self.main_window.updateSidebarButtons(self.main_window.sidebar.notification_btn))
        return notif_btn

    def _createUserContainer(self):
        """Create and return the user information container with username and logout."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(10)

        self.username_label = QLabel()
        self.updateUsername()
        self.username_label.setStyleSheet(
            """
            QLabel {
                color: #333;
                font-weight: bold;
                font-size: 14px;
            }
        """
        )
        layout.addWidget(self.username_label)

        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FF4444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF0000;
            }
        """
        )
        logout_btn.clicked.connect(self._handle_logout)
        layout.addWidget(logout_btn)

        return container

    def updateUsername(self):
        """Update the username display based on the current user."""
        if self.username_label:
            if self.main_window and hasattr(self.main_window, "current_user"):
                self.username_label.setText(
                    f"Welcome, {self.main_window.current_user}!"
                )
            else:
                self.username_label.setText("Welcome!")

    def _handle_logout(self):
        """Handle the logout button click with confirmation."""
        if self.main_window:
            reply = QMessageBox.question(
                self,
                "Logout",
                "Are you sure you want to logout?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.main_window.logout()


class SidebarButton(QPushButton):
    """
    Custom button widget for sidebar navigation.
    Provides consistent styling and behavior for sidebar buttons.
    """

    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(text, parent)
        self.initUI(icon_path)

    def initUI(self, icon_path):
        """Initialize the button's UI with icon and styling."""
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(24, 24))

        self.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding: 12px 20px;
                border: none;
                border-radius: 8px;
                margin: 4px 12px;
                color: #333;
                font-size: 15px;
                font-weight: 500;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: rgba(0, 180, 216, 0.08);
                color: #00B4D8;
            }
            QPushButton:checked {
                background-color: rgba(0, 180, 216, 0.15);
                color: #00B4D8;
                font-weight: 600;
            }
            QPushButton:checked:hover {
                background-color: rgba(0, 180, 216, 0.2);
            }
        """
        )
        self.setCheckable(True)
        self.setMinimumHeight(48)


class SidebarWidget(QWidget):
    """
    Widget that provides navigation functionality through a sidebar.
    Contains buttons for different sections of the application.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        """Initialize the sidebar UI with navigation buttons."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 15, 0, 15)
        layout.setSpacing(8)

        self.tasks_btn = SidebarButton("Tasks", get_image_path("tasks.png"))
        self.schedule_btn = SidebarButton("Schedule", get_image_path("monthly.png"))
        self.history_btn = SidebarButton("History", get_image_path("history.png"))
        self.notification_btn = SidebarButton("Notifications", get_image_path("notification.png"))

        self.tasks_btn.setChecked(True)

        for btn in [self.tasks_btn, self.schedule_btn, self.history_btn, self.notification_btn]:
            layout.addWidget(btn)
        layout.addStretch()

        self.setLayout(layout)
        self.setStyleSheet("QWidget { background-color: #E3F8FF; border-right: none; }")
        self.setFixedWidth(200)
        
        


class TaskItemWidget(QFrame):
    """
    Widget representing a single task item.
    Displays task information and provides actions for task management.
    """

    PRIORITY_COLORS = {
        "High": "#FF4444",
        "Medium": "#FF8C00",
        "Low": "#FFD700",
        "None": "#999",
    }

    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        if "username" not in task_data:
            task_data["username"] = (
                parent.current_user
                if parent and hasattr(parent, "current_user")
                else None
            )
        self.task_data = task_data
        self.main_window = parent
        self.extra_info_label = None
        self.checkDeadline()
        self.initUI()

    def checkDeadline(self):
        """Check if task deadline has passed and update status accordingly."""
        if self.task_data.get("status", "").startswith("due"):
            deadline_str = self.task_data.get("deadline", "")
            if deadline_str:
                try:
                    deadline = QDateTime.fromString(deadline_str, "yyyy-MM-dd HH:mm")
                    current = QDateTime.currentDateTime()

                    if deadline.isValid() and current > deadline:
                        self.task_data["status"] = "failed"
                        if self.main_window:
                            self.main_window.saveTasks()
                            
                            # Trigger notification for deadline passed
                            self._trigger_deadline_passed_notification()
                except Exception as e:
                    print(f"Error checking deadline: {e}")

    def _trigger_deadline_passed_notification(self):
        """Trigger a notification when a deadline has passed."""
        if self.main_window and hasattr(self.main_window, 'notification_system'):
            task_id = f"{self.task_data['name']}_{self.task_data['start_time']}_{self.task_data['deadline']}"
            self.main_window.notification_system.add_notification(
                task_id,
                f"Task '{self.task_data['name']}' has failed (deadline passed)!",
                "failed"
            )
            self.main_window.notification_system.notified_tasks.add(f"{task_id}_failed")

    def initUI(self):
        """Initialize the task item UI components and layout."""
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        # Left side - Task info
        top_layout.addLayout(self._createTaskInfo(), stretch=2)
        
        # Middle - Times layout
        top_layout.addLayout(self._createTimesLayout(), stretch=1)
        
        # Right side container for schedule, priority and status
        right_container = QVBoxLayout()
        right_container.setSpacing(0)
        right_container.setContentsMargins(0, 0, 0, 0)
        
        # Add schedule info if exists
        schedule = self.task_data.get("schedule", "")
        if schedule:
            schedule_label = QLabel(f"🔄scheduled: {schedule}")
            schedule_label.setStyleSheet("color: #666; font-size: 14px;")
            schedule_label.setContentsMargins(0, 8, 0, 8)  # Increase vertical padding
            schedule_label.setFixedHeight(32)  # Increase height
            schedule_label.setMinimumWidth(120)
            schedule_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            right_container.addWidget(schedule_label)
        
        # Create container for priority, status and kebab menu
        buttons_container = QWidget()
        buttons_container.setStyleSheet("background-color: white;")  # Set white background
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)
        
        # Add priority and status buttons
        priority_status_layout = QHBoxLayout()
        priority_status_layout.setSpacing(5)
        priority_status_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        priority_status_layout.addWidget(self._createPriorityButton())
        priority_status_layout.addWidget(self._createStatusButton())
        
        # Add kebab menu separately
        kebab_menu = self._createKebabMenu()
        kebab_menu.setFixedHeight(32)  # Match height with other buttons
        
        # Add layouts to buttons container
        buttons_layout.addLayout(priority_status_layout)
        buttons_layout.addWidget(kebab_menu)
        
        # Add buttons container to right container
        right_container.addWidget(buttons_container)
        
        # Add right container to top layout
        top_layout.addLayout(right_container)

        main_layout.addLayout(top_layout)
        self.setLayout(main_layout)
        self.setStyleSheet(
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

    def _createKebabMenu(self):
        """Create and return the kebab menu button with actions."""
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

        menu = QMenu(self)
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

        actions = [
            ("Update", get_image_path("edit.png")),
            ("Delete", get_image_path("delete.png")),
            ("Mark as Done", get_image_path("done.png")),
            ("Mark as Failed", get_image_path("failed.png")),
            ("Move to History", get_image_path("history.png")),
        ]

        for text, icon_path in actions:
            action = QAction(QIcon(icon_path), text, self)
            action.triggered.connect(lambda checked, t=text: self._handleAction(t))
            menu.addAction(action)

        kebab_btn.clicked.connect(
            lambda: menu.exec_(kebab_btn.mapToGlobal(kebab_btn.rect().bottomLeft()))
        )
        return kebab_btn

    def _handleAction(self, action):
        """Handle menu action selections."""
        if action == "Update":
            from update import TodoUpdater

            # Preserve username when updating task
            current_username = self.task_data.get("username")
            TodoUpdater.update_task(self, self._refreshWidget)
            if current_username:
                self.task_data["username"] = current_username
        elif action == "Delete":
            from delete import TodoDeleter

            TodoDeleter.delete_task(self, self._notifyParentOfChange)
        elif action == "Mark as Done":
            from update import TodoUpdater

            # Preserve username when marking as done
            current_username = self.task_data.get("username")
            TodoUpdater.mark_task_as_done(self, self._refreshWidget)
            if current_username:
                self.task_data["username"] = current_username
                
            # Trigger notification for task completion
            self._trigger_task_completion_notification()
        elif action == "Mark as Failed":
            from update import TodoUpdater

            # Preserve username when marking as failed
            current_username = self.task_data.get("username")
            TodoUpdater.mark_task_as_failed(self, self._refreshWidget)
            if current_username:
                self.task_data["username"] = current_username
                
            # Trigger notification for task failure
            self._trigger_task_failure_notification()
        elif action == "Move to History":
            from update import TodoUpdater

            TodoUpdater.move_task_to_history(self, self._notifyParentOfChange)

    def _trigger_task_completion_notification(self):
        """Trigger a notification for task completion."""
        if self.main_window and hasattr(self.main_window, 'notification_system'):
            task_id = f"{self.task_data['name']}_{self.task_data['start_time']}_{self.task_data['deadline']}"
            self.main_window.notification_system.add_notification(
                task_id,
                f"Task '{self.task_data['name']}' has been completed!",
                "done"
            )
            self.main_window.notification_system.notified_tasks.add(f"{task_id}_done")
            
    def _trigger_task_failure_notification(self):
        """Trigger a notification for task failure."""
        if self.main_window and hasattr(self.main_window, 'notification_system'):
            task_id = f"{self.task_data['name']}_{self.task_data['start_time']}_{self.task_data['deadline']}"
            self.main_window.notification_system.add_notification(
                task_id,
                f"Task '{self.task_data['name']}' has been marked as failed!",
                "failed"
            )
            self.main_window.notification_system.notified_tasks.add(f"{task_id}_failed")

    def _refreshWidget(self):
        """Refresh the widget's display after task data changes."""
        try:
            self.checkDeadline()

            if self.name_label:
                self.name_label.setText(self.task_data.get("name", ""))

            if self.desc_label:
                self.desc_label.setText(self.task_data.get("description", ""))

            if self.start_label:
                self.start_label.setText(
                    f"StartLine: {self.task_data.get('start_time', '')}"
                )

            if self.deadline_label:
                self.deadline_label.setText(
                    f"Deadline: {self.task_data.get('deadline', '')}"
                )

            if self.priority_btn:
                priority = self.task_data.get("priority", "None")
                self.priority_btn.setText(priority)
                self.priority_btn.setFixedHeight(32)  # Maintain fixed height
                self.priority_btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        background-color: {self.PRIORITY_COLORS.get(priority, "#999")};
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 3px 8px;
                        font-size: 12px;
                    }}
                    """
                )

            if self.status_btn:
                status = self.task_data.get("status", "due")
                status_text = "done" if "done" in status.lower() else "failed" if "failed" in status.lower() else "due"
                status_colors = {
                    "done": "#4CAF50",
                    "failed": "#FF4444",
                    "due": "#999999",
                }
                self.status_btn.setText(status_text)
                self.status_btn.setFixedHeight(32)  # Maintain fixed height
                self.status_btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        background-color: {status_colors.get(status_text, "#999999")};
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 3px 8px;
                        font-weight: bold;
                        font-size: 12px;
                    }}
                    """
                )

            # Notify parent of changes
            self._notifyParentOfChange()
            
            # Refresh schedule page if it exists
            if self.main_window and hasattr(self.main_window, 'schedule_widget'):
                self.main_window.schedule_widget.refreshSchedule()
        except Exception as e:
            print(f"Error refreshing widget: {e}")
            # Don't propagate the error to prevent crashes

    def _notifyParentOfChange(self):
        """Notify parent widget of task data changes."""
        try:
            if self.main_window and hasattr(self.main_window, 'task_manager'):
                self.main_window.task_manager.saveTasks()
                
                # Refresh schedule page if it exists
                if hasattr(self.main_window, 'schedule_widget'):
                    self.main_window.schedule_widget.refreshSchedule()
        except Exception as e:
            print(f"Error notifying parent of change: {e}")
            # Don't propagate the error to prevent crashes

    def _createTaskInfo(self):
        """Create and return the layout for task name and description."""
        info_layout = QVBoxLayout()

        self.name_label = QLabel(self.task_data.get("name", ""))
        self.name_label.setFont(QFont("Arial", 12, QFont.Bold))

        self.desc_label = QLabel(self.task_data.get("description", ""))
        self.desc_label.setStyleSheet("color: #666;")

        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.desc_label)

        return info_layout

    def _createTimesLayout(self):
        """Create and return the layout for start and deadline times."""
        times_layout = QVBoxLayout()

        self.start_label = QLabel(f"StartLine: {self.task_data.get('start_time', '')}")
        self.deadline_label = QLabel(f"Deadline: {self.task_data.get('deadline', '')}")

        times_layout.addWidget(self.start_label)
        times_layout.addWidget(self.deadline_label)

        return times_layout

    def _createPriorityButton(self):
        """Create and return the priority indicator button."""
        priority = self.task_data.get("priority", "None")
        self.priority_btn = QPushButton(priority)
        self.priority_btn.setFixedWidth(80)
        self.priority_btn.setFixedHeight(32)  # Set fixed height
        self.priority_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.PRIORITY_COLORS.get(priority, "#999")};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 5px;
                font-size: 12px;
            }}
        """
        )
        return self.priority_btn

    def _createStatusButton(self):
        """Create and return the status indicator button."""
        status = self.task_data.get("status", "due")
        if "done" in status.lower():
            display_text = "done"
            bg_color = "#4CAF50"
        elif "failed" in status.lower():
            display_text = "failed"
            bg_color = "#FF4444"
        else:
            display_text = "due"
            bg_color = "#999999"

        self.status_btn = QPushButton(display_text)
        self.status_btn.setFixedWidth(80)
        self.status_btn.setFixedHeight(32)  # Set fixed height
        self.status_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 5px;
                font-weight: bold;
                font-size: 12px;
            }}
        """
        )
        return self.status_btn


class LoadingWidget(QWidget):
    """
    Widget that displays a loading animation and message
    while tasks are being refreshed.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        """Initialize the loading widget UI components."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.loading_label = QLabel()
        self.movie = QMovie(get_image_path("loading.gif"))
        self.loading_label.setMovie(self.movie)
        self.loading_label.setAlignment(Qt.AlignCenter)

        text_label = QLabel("Refreshing tasks...")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet(
            """
            QLabel {
                color: #666;
                font-size: 14px;
                margin-top: 10px;
            }
        """
        )

        layout.addWidget(self.loading_label)
        layout.addWidget(text_label)
        self.setLayout(layout)

    def showEvent(self, event):
        """Start the animation when widget becomes visible."""
        self.movie.start()
        super().showEvent(event)

    def hideEvent(self, event):
        """Stop the animation when widget becomes hidden."""
        self.movie.stop()
        super().hideEvent(event)
