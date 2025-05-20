from PyQt5 import QtWidgets, QtCore, QtGui
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
    QMenu,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import QTime, QDate, QDateTime
import os
import time
from _sopian.path_utils import get_image_path, get_database_path


class IconManager:
    """Class untuk mengelola dan preload semua ikon"""
    _instance = None
    _icons = {}
    _required_icons = [
        "Calender_icon.png",
        "Flag_icon.png",
        "Reminder_icon.png",
        "HighPriority_icon.png",
        "MediumPriority_icon.png",
        "LowPriority_icon.png"
    ]
    _icon_size = QSize(24, 24)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IconManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def preload_icons(cls):
        """Preload semua ikon yang dibutuhkan"""
        if not cls._icons:  # Only preload if not already done
            start_time = time.time()
            for icon_file in cls._required_icons:
                icon_path = get_image_path(icon_file)
                if os.path.exists(icon_path):
                    # Load dan cache pixmap dengan ukuran yang optimal
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        # Scale pixmap ke ukuran yang dibutuhkan
                        pixmap = pixmap.scaled(cls._icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        # Convert ke format yang lebih efisien
                        image = pixmap.toImage()
                        image = image.convertToFormat(QImage.Format_ARGB32_Premultiplied)
                        pixmap = QPixmap.fromImage(image)
                        cls._icons[icon_file] = QIcon(pixmap)
                    else:
                        cls._icons[icon_file] = QIcon()
                else:
                    cls._icons[icon_file] = QIcon()
            end_time = time.time()

    @classmethod
    def get_icon(cls, icon_file):
        """Get icon from cache"""
        return cls._icons.get(icon_file, QIcon())

class DateTimeDialog(QDialog):
    def __init__(self, parent=None, title="Select Date and Time", is_start_time=False, deadline=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.is_start_time = is_start_time
        self.deadline = deadline
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate.currentDate())
        layout.addWidget(QLabel("Select Date:"))
        layout.addWidget(self.calendar)

        # Time widget
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())
        layout.addWidget(QLabel("Select Time:"))
        layout.addWidget(self.time_edit)

        # Button container untuk tombol-tombol
        button_container = QHBoxLayout()
        
        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_selection)
        self.reset_button.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                text-align: center;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f44336;
                color: white;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        
        # Tambahkan tombol ke container
        button_container.addWidget(self.reset_button)
        button_container.addWidget(button_box)
        
        layout.addLayout(button_container)
        self.setLayout(layout)

    def reset_selection(self):
        """Reset pilihan tanggal dan waktu ke nilai default dan tutup dialog."""
        if self.is_start_time:
            self.calendar.setSelectedDate(QDate.currentDate())
            self.time_edit.setTime(QTime.currentTime())
        self.reject()


    def validate_and_accept(self):
        selected_date = self.calendar.selectedDate()
        selected_time = self.time_edit.time()
        selected_datetime = f"{selected_date.toString('yyyy-MM-dd')} {selected_time.toString('HH:mm')}"

        if not self.is_start_time and self.deadline:
            #jika validasi deadline dan start time kosong, deadline bisa diisi apa saja
            if self.deadline not in ["Start time",""]:
                start_date =QDate.fromString(self.deadline.split(" ")[0], "yyyy-MM-dd")
                start_time = QTime.fromString(self.deadline.split(" ")[1], "HH:mm")

                if selected_date < start_date or (selected_date == start_date and selected_time <= start_time):
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        "deadline must be later than start time!"
                    )
                    return

        self.accept()

    def get_datetime(self):
        selected_date = self.calendar.selectedDate()
        selected_time = self.time_edit.time()
        return f"{selected_date.toString('yyyy-MM-dd')} {selected_time.toString('HH:mm')}"


## main program ##
class AddTaskWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        start_time = time.time()
        super().__init__(parent)
        
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setObjectName("AddTodo")
        self.setMinimumWidth(855)
        self.setMaximumWidth(855)

        # Setup main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Task Name Input
        self.TaskName = QtWidgets.QLineEdit()
        self.TaskName.setObjectName("TaskName")
        self.TaskName.setPlaceholderText("Task Name")
        self.TaskName.textChanged.connect(self._delayed_validate)
        main_layout.addWidget(self.TaskName)

        # Task Description Input
        self.DescTask = QtWidgets.QTextEdit()
        self.DescTask.setObjectName("DescTask")
        self.DescTask.setPlaceholderText("Description")
        self.DescTask.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.DescTask.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.DescTask.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        main_layout.addWidget(self.DescTask)

        # Setup buttons
        self._setup_buttons(main_layout)

        # Setup validation timer
        self._validation_timer = QtCore.QTimer()
        self._validation_timer.setSingleShot(True)
        self._validation_timer.timeout.connect(self.validate_input)
        
        end_time = time.time()

    def _setup_buttons(self, main_layout):
        """Setup all buttons and their containers"""
        # Container untuk tombol-tombol utama
        self.button_container = QtWidgets.QWidget()
        self.button_layout = QtWidgets.QHBoxLayout(self.button_container)
        self.button_layout.setSpacing(10)
        self.button_layout.setContentsMargins(0, 0, 0, 0)

        # Get icon manager instance
        icon_manager = IconManager()

        # Buttons (Start Time, Deadline, Priority, Reminder)
        self.StartTime = self.create_button("StartTime", "Calender_icon.png", "Start time", icon_manager)
        self.Deadline = self.create_button("Deadline", "Calender_icon.png", "Deadline", icon_manager)
        self.Priority = self.create_button("Priority", "Flag_icon.png", "Priority", icon_manager)
        self.Reminder = self.create_button("Reminder", "Reminder_icon.png", "Reminder", icon_manager)

        self.button_layout.addWidget(self.StartTime)
        self.button_layout.addWidget(self.Deadline)
        self.button_layout.addWidget(self.Priority)
        self.button_layout.addWidget(self.Reminder)
        self.button_layout.addStretch()
        main_layout.addWidget(self.button_container)

        # Line Separator
        self.line_3 = QtWidgets.QFrame()
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        main_layout.addWidget(self.line_3)

        # Container untuk tombol aksi
        self.action_container = QtWidgets.QWidget()
        self.action_layout = QtWidgets.QHBoxLayout(self.action_container)
        self.action_layout.setSpacing(10)
        self.action_layout.setContentsMargins(0, 0, 0, 0)

        self.Cancel = self.create_action_button("Cancel", "Cancel")
        self.AddTask = self.create_action_button("Add Task", "AddTask")
        self.AddTask.setEnabled(False)

        self.action_layout.addStretch()
        self.action_layout.addWidget(self.Cancel)
        self.action_layout.addWidget(self.AddTask)
        main_layout.addWidget(self.action_container)

        # Connect action buttons
        self.Cancel.clicked.connect(self.cancel_toggle)
        self.AddTask.clicked.connect(self.set_save_handler)
        self.StartTime.clicked.connect(lambda: self.show_datetime_dialog(self.StartTime))
        self.Deadline.clicked.connect(lambda: self.show_datetime_dialog(self.Deadline))

        # Create dropdown menus
        self.priority_dropdown = self.create_dropdown_menu(self.Priority, ["None", "Low", "Medium", "High"], icon_manager)
        self.reminder_dropdown = self.create_dropdown_menu(self.Reminder, ["None", "5 minutes before", "15 minutes before", "30 minutes before", "1 hour before"], icon_manager)

        # Connect dropdown buttons
        self.Priority.clicked.connect(lambda: self.toggle_dropdown(self.priority_dropdown, self.Priority))
        self.Reminder.clicked.connect(lambda: self.toggle_dropdown(self.reminder_dropdown, self.Reminder))

    def create_button(self, name, icon_file, text, icon_manager):
        """Helper untuk membuat QPushButton dengan ikon dan ukuran yang dinamis."""
        button = QtWidgets.QPushButton(text)
        button.setObjectName(name)
        button.setMinimumWidth(100)
        button.setFixedHeight(28)
        button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
        # Get icon from manager
        icon = icon_manager.get_icon(icon_file)
        button.setIcon(icon)
        button.setIconSize(IconManager._icon_size)
        
        button.setStyleSheet(f"""
            QPushButton {{
                padding: 5px 10px;
                text-align: left;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }}
            QPushButton:hover {{
                background-color: #f0f0f0;
            }}
        """)
        
        return button

    def create_action_button(self, name, object_name):
        button = QtWidgets.QPushButton(name)
        button.setObjectName(object_name)
        button.setFixedWidth(93)
        button.setFixedHeight(28)
        button.setStyleSheet(f"""
            QPushButton {{
                padding: 5px 10px;
                text-align: center;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }}
            QPushButton:hover {{
                background-color: #f0f0f0;
            }}
            QPushButton#AddTask {{
                background-color: #2196F3;
                color: white;
                border: none;
            }}
            QPushButton#AddTask:hover {{
                background-color: #1976D2;
            }}
            QPushButton#AddTask:disabled {{
                background-color: #BDBDBD;
            }}
            QPushButton#Cancel {{
                background-color: #f44336;
                color: white;
                border: none;
            }}
            QPushButton#Cancel:hover {{
                background-color: #da190b;
            }}
        """)
        return button

    def create_dropdown_menu(self, button, items, icon_manager):
        """Helper untuk membuat menu dropdown."""
        menu = QMenu(self)
        if button == self.Priority:
            priority_icons = {
                "None": icon_manager.get_icon("Flag_icon.png"),
                "High": icon_manager.get_icon("HighPriority_icon.png"),
                "Medium": icon_manager.get_icon("MediumPriority_icon.png"),
                "Low": icon_manager.get_icon("LowPriority_icon.png")
            }
            for item in items:
                action = menu.addAction(item)
                action.setIcon(priority_icons[item])
                action.triggered.connect(lambda checked, text=item: self.handle_dropdown_selection(button, text))
        else:
            for item in items:
                action = menu.addAction(item)
                action.triggered.connect(lambda checked, text=item: self.handle_dropdown_selection(button, text))
        return menu

    def toggle_dropdown(self, menu, button):
        self.hide_all_dropdowns()
        pos = button.mapToGlobal(button.rect().bottomLeft())
        menu.exec_(pos)

    def hide_all_dropdowns(self):
        self.priority_dropdown.hide()
        self.reminder_dropdown.hide()

    def handle_dropdown_selection(self, button, text):
        """Handle pemilihan item dari dropdown menu."""
        if button == self.Priority:
            icon_manager = IconManager()
            priority_icons = {
                "None": icon_manager.get_icon("Flag_icon.png"),
                "High": icon_manager.get_icon("HighPriority_icon.png"),
                "Medium": icon_manager.get_icon("MediumPriority_icon.png"),
                "Low": icon_manager.get_icon("LowPriority_icon.png")
            }
            button.setText(text if text != "None" else "Priority")
            button.setIcon(priority_icons[text])
            button.setIconSize(IconManager._icon_size)
        elif button == self.Reminder:
            button.setText(text if text != "None" else "Reminder")

    def validate_input(self):
        self.AddTask.setEnabled(bool(self.TaskName.text().strip()))

    def clear_inputs(self):
        self.TaskName.clear()
        self.DescTask.clear()
        self.StartTime.setText("Start time")
        self.Deadline.setText("Deadline")
        self.Priority.setText("Priority")
        self.Reminder.setText("Reminder")
        self.AddTask.setEnabled(False)
        self.hide_all_dropdowns()

    def cancel_toggle(self):
        self.clear_inputs()
        parent_dialog = self.parent()
        if parent_dialog and isinstance(parent_dialog, QDialog):
            parent_dialog.reject()
        else:
            self.hide()

    def show_datetime_dialog(self, button):
        title = "Select Start Time" if button == self.StartTime else "Select Deadline"
        is_start_time = button == self.StartTime
        current_datetime = QDateTime.currentDateTime()
        default_time = f"{current_datetime.date().toString('yyyy-MM-dd')} {current_datetime.time().toString('HH:mm')}"
        dialog = DateTimeDialog(self, title, is_start_time, default_time)
        if dialog.exec_():
            selected_datetime = dialog.get_datetime()
            button.setText(selected_datetime)
            if not is_start_time:
                if not self.validate_deadline():
                    button.setText("Deadline")
        else:
            if is_start_time:
                button.setText("Start time")
            else:
                button.setText("Deadline")

    def validate_start_time(self):
        if self.StartTime.text() != "Start time" and self.Deadline.text() != "Deadline":
            start_date = QDate.fromString(self.StartTime.text().split(" ")[0], "yyyy-MM-dd")
            start_time = QTime.fromString(self.StartTime.text().split(" ")[1], "HH:mm")
            deadline_date = QDate.fromString(self.Deadline.text().split(" ")[0], "yyyy-MM-dd")
            deadline_time = QTime.fromString(self.Deadline.text().split(" ")[1], "HH:mm")
            if start_date > deadline_date or (start_date == deadline_date and start_time >= deadline_time):
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Start time cannot be later than or equal to deadline!"
                )
                self.StartTime.setText("Start time")

    def validate_deadline(self):
        if self.Deadline.text() in ["Deadline", ""]:
            return True
        if self.StartTime.text() in ["Start time", ""]:
            current_datetime = QDateTime.currentDateTime()
            start_date = current_datetime.date()
            start_time = current_datetime.time()
        else:
            start_date = QDate.fromString(self.StartTime.text().split(" ")[0], "yyyy-MM-dd")
            start_time = QTime.fromString(self.StartTime.text().split(" ")[1], "HH:mm")
        deadline_date = QDate.fromString(self.Deadline.text().split(" ")[0], "yyyy-MM-dd")
        deadline_time = QTime.fromString(self.Deadline.text().split(" ")[1], "HH:mm")
        if deadline_date < start_date or (deadline_date == start_date and deadline_time <= start_time):
            QMessageBox.warning(
                self,
                "Validation Error",
                "Deadline cannot be earlier than or equal to start time!"
            )
            self.Deadline.setText("Deadline")
            return False
        return True

    def set_save_handler(self, save_handler):
        self.save_handler = save_handler
        self.AddTask.clicked.disconnect()
        self.AddTask.clicked.connect(self._handle_save)

    def _handle_save(self):
        try:
            if not self.TaskName.text().strip():
                QMessageBox.warning(self, "Error", "Task name is required")
                return
            if not hasattr(self, 'save_handler') or not callable(self.save_handler):
                QMessageBox.critical(self, "Error", "Save handler is not properly set")
                return
            if not self.validate_deadline():
                return
            parent_dialog = self.parent()
            if parent_dialog and isinstance(parent_dialog, QDialog):
                self.save_handler()
                parent_dialog.accept()
            else:
                QMessageBox.critical(self, "Error", "Invalid dialog parent")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
            return

    def _delayed_validate(self):
        self._validation_timer.start(300)
