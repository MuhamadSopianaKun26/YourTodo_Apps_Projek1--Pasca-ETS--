from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QCalendarWidget,
    QRadioButton,
    QHBoxLayout,
    QLabel,
    QTimeEdit,
    QMessageBox,
    QDialogButtonBox,
)
from PyQt5.QtCore import QTime, QDate, Qt, QDateTime
from PyQt5.QtGui import QFont, QPixmap
from Add_Task import AddTaskWidget
from path_utils import get_image_path

class BaseDialog(QDialog):
    """
    Base dialog class providing common initialization functionality
    for all dialog windows in the application.
    """

    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)


class ImageDialog(BaseDialog):
    """
    Dialog window displaying an image with a message.
    Used as a fun interaction before task creation.
    """

    def __init__(self, parent=None):
        super().__init__(parent, "Bayar Dulu Bos!!")
        self._setup_ui()

    def _setup_ui(self):
        """Initialize and set up the dialog's UI components."""
        self.textLabel = QLabel("Bayar dulu bos!!", self)
        self.textLabel.setFont(QFont("Arial", 16, QFont.Bold))
        self.textLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.textLabel)

        self.imageLabel = QLabel(self)
        pixmap = QPixmap(get_image_path("img.png"))
        if pixmap.isNull():
            self.imageLabel.setText("Gambar tidak ditemukan!")
        else:
            self.imageLabel.setPixmap(pixmap)
        self.layout.addWidget(self.imageLabel)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok, self)
        self.buttonBox.accepted.connect(self.accept)
        self.layout.addWidget(self.buttonBox)


class TaskDialog(BaseDialog):
    """
    Dialog for creating or editing a task.
    Provides form fields for all task properties and validates input.
    """

    def __init__(self, parent=None, task_data=None):
        super().__init__(parent, "Add New Task")
        try:
            self.task_data = task_data or {}
            self._setup_ui()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating task: {e}")
            self.reject()

    def _setup_ui(self):
        """Initialize and set up all task form components."""
        self.add_task_widget = AddTaskWidget(self)
        self.layout.addWidget(self.add_task_widget)

        # Set task data if available
        if self.task_data:
            self.add_task_widget.set_task_data(self.task_data)

        # Apply stylesheet directly
        self.add_task_widget.setStyleSheet("""
QWidget#AddTodo {
	border : 1px solid rgb(180, 180, 180);
	border-radius: 20px;
	background-color: rgb(242, 255, 254);
}

QLineEdit#TaskName {
	background-color : Transparent;
	border: none;
	font-size : 18px;
	font-weight: bold;
}

QTextEdit#DescTask {
	background-color : Transparent;
	border: none;
	font-size : 16px;
}

QPushButton#Deadline,#StartTime,#Priority,#Reminder {
	Background-color : rgb(244, 255, 253);
	border: 1px solid  rgb(180, 180, 180);
	color: rgb(180, 180, 180);
	font-family: Sagoe UI;
    font-size: 12px;
	font-weight: 600;
	padding: 0px 10px;
}

QPushButton#Deadline:hover,#StartTime:hover,#Priority:hover,#Reminder:hover {
	background-color:  rgb(210, 210, 210);
}

QPushButton#Cancel {
	background-color : rgb(240, 240, 240);
	font-family : Sagoe UI;
    border-radius : 10px;
}

QPushButton#AddTask{
	background-color : rgb(29, 195, 255);
	font-family : Sagoe UI;
    border-radius : 10px;
}

QPushButton#Cancel:hover{
	background-color:  rgb(210, 210, 210);
}

QPushButton#AddTask:Hover{
	background-color : rgb(20, 141, 181);
}
""")

        # Set the save handler to validate_and_accept
        self.add_task_widget.set_save_handler(self.validate_and_accept)

        self.resize(860, 300)
    
    def validate_and_accept(self):
        """Validate all form inputs before accepting the dialog."""
        if not self.add_task_widget.TaskName.text().strip():
            QMessageBox.warning(self, "Error", "Task name is required")
            return
        
        if not self.add_task_widget.validate_deadline():
            return

        # Get task data before accepting
        task_data = self.get_task_data()
        if task_data:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to get task data")

    def get_task_data(self):
        """Get the task data from the form fields."""
        try:
            #curent date :
            current_datetime = QDateTime.currentDateTime()
            default_start = f"{current_datetime.date().toString('yyyy-MM-dd')} {current_datetime.time().toString('HH:mm')}"

            start_time_text = self.add_task_widget.StartTime.text()
            deadline_text = self.add_task_widget.Deadline.text()

            if start_time_text in ["Start time", ""]:
                start_time = default_start
            else: 
                try:
                    date_part, time_part = start_time_text.split(" ")
                    QDate.fromString(date_part, "yyyy-MM-dd")
                    QTime.fromString(time_part, "HH:mm")
                    start_time = start_time_text
                except:
                    start_time = default_start
                    
            if deadline_text == "Deadline":
                deadline = ""
            else:
                try:
                    date_part, time_part = deadline_text.split(" ")
                    QDate.fromString(date_part, "yyyy-MM-dd")  # Validasi format tanggal
                    QTime.fromString(time_part, "HH:mm")       # Validasi format waktu
                    deadline = deadline_text
                except:
                    deadline = ""

            # Get priority and reminder values
            priority_text = self.add_task_widget.Priority.text()
            reminder_text = self.add_task_widget.Reminder.text()

            task_data = {
                "name": self.add_task_widget.TaskName.text() or "",
                "description": self.add_task_widget.DescTask.toPlainText() or "",
                "start_time": start_time,
                "deadline": deadline,
                "priority": priority_text if priority_text != "Priority" else "None",
                "reminder": reminder_text if reminder_text != "Reminder" else "None",
                "status": "due",
                "schedule": "None",  # Always set schedule to None
            }

            # Preserve username if it exists in the original task data
            if hasattr(self, "task_data") and "username" in self.task_data:
                task_data["username"] = self.task_data["username"]

            return task_data
    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error getting task data: {e}")
            return None


class TodoCreator:
    """
    Static class for handling task creation workflow.
    Manages the display of dialogs and task data handling.
    """

    @staticmethod
    def add_task(parent_widget, save_callback):
        """
        Show image dialog and then task dialog for creating a new task.
        Calls the save_callback with the task data if task creation is successful.
        """
        imageDialog = ImageDialog(parent_widget)
        if imageDialog.exec_():
            dialog = TaskDialog(parent_widget)
            if dialog.exec_():
                task_data = dialog.get_task_data()
                save_callback(task_data)
