from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QMessageBox,
    QStackedWidget,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon
import sys
import time

from _darrel.create import TodoCreator
from _sopian.main_components import (
    HeaderWidget, 
    SidebarWidget, 
    TaskItemWidget, 
    LoadingWidget,
)
from _praditama.auth import LoginDialog
from _fauzan.history import HistoryWidget
from _darrel.task import TaskManager
from _rizqi.notification import NotificationWidget, NotificationSystem
from _sopian.schedule import ScheduleWidget
from _praditama.welcome_screen import WelcomeScreen
from _sopian.Add_Task import IconManager

def log_time(message):
    """Helper function untuk logging waktu"""
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

class ToDoApp(QWidget):
    """
    Main application window for the Todo application.
    Handles user authentication, task management, and UI interactions.
    """

    def __init__(self):
        super().__init__()
        self.current_user = None
        self.taskTable = None
        self.task_manager = TaskManager(self)
        self.notification_system = None
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
        # Preload icons saat aplikasi pertama kali dibuka
        start_time = time.time()
        IconManager.preload_icons()
        end_time = time.time()
        log_time(f"Application startup completed in {end_time - start_time:.3f} seconds")
        self.initUI()

    def initUI(self):
        """Initialize the main user interface components and layout."""
        self.setWindowTitle("YourTodo")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #F0FBFF;")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header = HeaderWidget(self)
        main_layout.addWidget(self.header)
        main_layout.addLayout(self._setupContentArea())

        self.setLayout(main_layout)

    def _setupContentArea(self):
        """Set up the main content area with sidebar and stacked widget."""
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.sidebar = SidebarWidget()
        content_layout.addWidget(self.sidebar)

        self.stacked_widget = QStackedWidget()
        self._setupStackedWidgets()
        content_layout.addWidget(self.stacked_widget, stretch=1)

        self._connectSidebarButtons()

        return content_layout

    def _setupStackedWidgets(self):
        """Initialize and set up all section widgets in the stacked widget."""
        self.history_widget = None
        self.setupSimpleWidget(self.history_widget, "History")

        self.tasks_widget = self.task_manager.setupTasksWidget()
        self.stacked_widget.addWidget(self.tasks_widget)

        self.schedule_widget = ScheduleWidget(self)
        self.stacked_widget.addWidget(self.schedule_widget)

        self.notification_widget = NotificationWidget(self)
        self.stacked_widget.addWidget(self.notification_widget)

        self.task_manager.loadTasks()

    def _connectSidebarButtons(self):
        """Connect sidebar buttons to their respective sections and set up button behavior."""
        button_sections = {
            self.sidebar.tasks_btn: "tasks",
            self.sidebar.history_btn: "history",
            self.sidebar.schedule_btn: "schedule",
            self.sidebar.notification_btn: "notifications",
        }

        for button, section in button_sections.items():
            button.clicked.connect(lambda checked, s=section: self.showSection(s))

        self.sidebar_buttons = list(button_sections.keys())
        for button in self.sidebar_buttons:
            button.clicked.connect(
                lambda checked, btn=button: self.updateSidebarButtons(btn)
            )

    def setupSimpleWidget(self, widget, text):
        """Set up a simple widget with centered text header."""
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        header_label = QLabel(text)
        header_label.setFont(QFont("Arial", 24, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("color: #333;")

        layout.addWidget(header_label)
        layout.addStretch()

    def authenticate(self):
        """Show login dialog and authenticate user. Returns True if successful."""
        login_dialog = LoginDialog()
        if login_dialog.exec_():
            self.current_user = login_dialog.username
            if hasattr(self, "header"):
                self.header.updateUsername()
                
            self.history_widget = HistoryWidget(self.current_user)
            self.stacked_widget.addWidget(self.history_widget)
            
            # Initialize notification system after user login
            if not self.notification_system:
                self.notification_system = NotificationSystem(self)
                self.notification_widget.notification_system = self.notification_system
            else:
                # Update the current user in the notification system
                self.notification_system.main_app = self
            
            self.task_manager.loadTasks()
            self.show()
            return True
        return False

    def showSection(self, section):
        """Switch to the specified section in the stacked widget."""
        section_widgets = {
            "tasks": self.tasks_widget,
            "history": self.history_widget,
            "schedule": self.schedule_widget,
            "notifications": self.notification_widget,
        }
        if section in section_widgets and section_widgets[section] is not None:
            self.stacked_widget.setCurrentWidget(section_widgets[section])
            if section == "history":
                self.history_widget.update_display()
            elif section == "notifications":
                self.notification_widget.loadNotifications()
            elif section == "schedule":
                # Refresh schedule page when schedule button is clicked
                self.schedule_widget.refreshSchedule()
            elif section == "tasks":
                # Check and add scheduled tasks when switching to tasks page
                self.schedule_widget.checkAndAddScheduledTasks()
                self.task_manager.refreshTasks()
        else:
            # Handle case where widget might not be initialized yet
            pass

    def updateSidebarButtons(self, clicked_button):
        """Update the checked state of sidebar buttons."""
        for button in self.sidebar_buttons:
            button.setChecked(button == clicked_button)

    def logout(self):
        """Handle user logout and return to login screen."""
        self.task_manager.saveTasks()
        
        # Stop notification timer if it exists
        if self.notification_system and hasattr(self.notification_system, 'timer'):
            self.notification_system.timer.stop()
            
        self.current_user = None

        if hasattr(self, "header"):
            self.header.updateUsername()

        if self.task_manager.task_list_layout:
            while self.task_manager.task_list_layout.count():
                item = self.task_manager.task_list_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        self.hide()

        if not self.authenticate():
            QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Show welcome screen first
    welcome_screen = WelcomeScreen()
    welcome_screen.show()
    
    # Create main window but don't show it yet
    window = ToDoApp()
    
    # Set up timer to close welcome screen and show login after 4 seconds
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(lambda: (welcome_screen.close(), window.authenticate()))
    timer.start(4000)  # 4000 milliseconds = 4 seconds
    
    sys.exit(app.exec_())
