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
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTime, QDate, QDateTime
import os
from _sopian.path_utils import get_image_path, get_database_path


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
        super().__init__(parent)
        
        self.setGeometry(QtCore.QRect(110, 190, 855, 290))
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setObjectName("AddTodo")
        # Prevent horizontal scrolling
        self.setMaximumWidth(855)
        self.setMinimumWidth(855)

        # Task Name Input
        self.TaskName = QtWidgets.QLineEdit(self)
        self.TaskName.setGeometry(QtCore.QRect(20, 20, 791, 21))
        self.TaskName.setObjectName("TaskName")
        self.TaskName.setPlaceholderText("Task Name")
        self.TaskName.textChanged.connect(self.validate_input)

        # Task Description Input
        self.DescTask = QtWidgets.QTextEdit(self)
        self.DescTask.setGeometry(QtCore.QRect(20, 50, 791, 61))
        self.DescTask.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.DescTask.setObjectName("DescTask")
        self.DescTask.setPlaceholderText("Description")
        # Enable vertical scrolling only for description
        self.DescTask.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.DescTask.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.DescTask.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)

        # Line Separator
        self.line_3 = QtWidgets.QFrame(self)
        self.line_3.setGeometry(QtCore.QRect(20, 160, 801, 16))
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")

        # Container untuk tombol-tombol utama
        self.button_container = QtWidgets.QWidget(self)
        self.button_container.setGeometry(QtCore.QRect(20, 130, 801, 28))
        self.button_container.setObjectName("button_container")
        
        # Layout horizontal untuk tombol-tombol utama
        self.button_layout = QtWidgets.QHBoxLayout(self.button_container)
        self.button_layout.setSpacing(10)
        self.button_layout.setContentsMargins(0, 0, 0, 0)

        # Buttons (Start Time, Deadline, Priority, Reminder)
        icon_path = get_image_path("")
        self.StartTime = self.create_button("StartTime", get_image_path("Calender_icon.png"), "Start time")
        self.Deadline = self.create_button("Deadline", get_image_path("Calender_icon.png"), "Deadline")
        self.Priority = self.create_button("Priority", get_image_path("Flag_icon.png"), "Priority")
        self.Reminder = self.create_button("Reminder", get_image_path("Reminder_icon.png"), "Reminder")

        # Tambahkan tombol ke layout utama
        self.button_layout.addWidget(self.StartTime)
        self.button_layout.addWidget(self.Deadline)
        self.button_layout.addWidget(self.Priority)
        self.button_layout.addWidget(self.Reminder)
        self.button_layout.addStretch()

        # Container untuk tombol aksi
        self.action_container = QtWidgets.QWidget(self)
        self.action_container.setGeometry(QtCore.QRect(20, 180, 801, 28))
        self.action_container.setObjectName("action_container")
        
        # Layout horizontal untuk tombol aksi
        self.action_layout = QtWidgets.QHBoxLayout(self.action_container)
        self.action_layout.setSpacing(10)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        
        # Buttons (Add & Cancel) dengan style yang baru
        self.Cancel = self.create_action_button("Cancel", "Cancel")
        self.AddTask = self.create_action_button("Add Task", "AddTask")
        self.AddTask.setEnabled(False)
        
        # Tambahkan tombol aksi ke layout
        self.action_layout.addStretch()
        self.action_layout.addWidget(self.Cancel)
        self.action_layout.addWidget(self.AddTask)

        # Connect action buttons
        self.Cancel.clicked.connect(self.cancel_toggle)
        self.AddTask.clicked.connect(self.set_save_handler)
        self.StartTime.clicked.connect(lambda: self.show_datetime_dialog(self.StartTime))
        self.Deadline.clicked.connect(lambda: self.show_datetime_dialog(self.Deadline))
        
        # Create dropdown menus
        self.priority_dropdown = self.create_dropdown_menu(self.Priority, ["None", "Low", "Medium", "High"])
        self.reminder_dropdown = self.create_dropdown_menu(self.Reminder, ["None", "5 minutes before", "15 minutes before", "30 minutes before", "1 hour before"])

        # Connect dropdown buttons
        self.Priority.clicked.connect(lambda: self.toggle_dropdown(self.priority_dropdown, self.Priority))
        self.Reminder.clicked.connect(lambda: self.toggle_dropdown(self.reminder_dropdown, self.Reminder))

    def set_save_handler(self, save_handler):
        """Terima refrensi method dari parrent widget"""
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

            # Validasi deadline sebelum menyimpan
            if not self.validate_deadline():
                return

            # Get parent dialog
            parent_dialog = self.parent()
            if parent_dialog and isinstance(parent_dialog, QDialog):
                # Call the save handler first
                self.save_handler()
                # Then accept the dialog
                parent_dialog.accept()
            else:
                QMessageBox.critical(self, "Error", "Invalid dialog parent")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
            # Don't close the dialog if there's an error
            return

    def create_button(self, name, icon_file, text):
        """Helper untuk membuat QPushButton dengan ikon dan ukuran yang dinamis."""
        button = QtWidgets.QPushButton(text)
        button.setObjectName(name)
        button.setMinimumWidth(100)
        button.setFixedHeight(28)
        button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
        icon_path = get_image_path(icon_file)
        if not os.path.exists(icon_path):
            print(f"Icon not found: {icon_path}")  # Debug
            icon = QIcon()  # Gunakan ikon kosong jika file tidak ada
        else:
            icon = QIcon(icon_path)
        # Set ikon
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(icon_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        button.setIcon(icon)
        
        # Set style untuk padding dan alignment
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
        """Helper untuk membuat tombol aksi (Add Task & Cancel)."""
        button = QtWidgets.QPushButton(name)
        button.setObjectName(object_name)
        button.setFixedWidth(93)
        button.setFixedHeight(28)
        
        # Set style khusus untuk tombol aksi
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

    def create_dropdown_menu(self, button, items):
        """Helper untuk membuat menu dropdown."""
        menu = QMenu(self)
        
        # Khusus untuk dropdown priority
        if button == self.Priority:
            # Dictionary untuk mengaitkan prioritas dengan ikon
            priority_icons = {
                "None": get_image_path("Flag_icon.png"),  # Kembali ke ikon default
                "High": get_image_path("HighPriority_icon.png"),
                "Medium": get_image_path("MediumPriority_icon.png"),
                "Low": get_image_path("LowPriority_icon.png")
            }
            
            for item in items:
                action = menu.addAction(item)
                # Set ikon untuk setiap item
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(priority_icons[item]), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                action.setIcon(icon)
                action.triggered.connect(lambda checked, text=item: self.handle_dropdown_selection(button, text))
        else:
            # Untuk dropdown lainnya (reminder dan repeated)
            for item in items:
                action = menu.addAction(item)
                action.triggered.connect(lambda checked, text=item: self.handle_dropdown_selection(button, text))
        
        return menu

    def toggle_dropdown(self, menu, button):
        """Toggle visibility of dropdown menu."""
        # Hide all other dropdowns first
        self.hide_all_dropdowns()
        
        # Show the clicked dropdown
        pos = button.mapToGlobal(button.rect().bottomLeft())
        menu.exec_(pos)

    def hide_all_dropdowns(self):
        """Hide all dropdown menus."""
        self.priority_dropdown.hide()
        self.reminder_dropdown.hide()

    def handle_dropdown_selection(self, button, text):
        """Handle pemilihan item dari dropdown menu."""
        if button == self.Priority:
            # Dictionary untuk mengaitkan prioritas dengan ikon
            priority_icons = {
                "None": get_image_path("Flag_icon.png"),  # Kembali ke ikon default
                "High": get_image_path("HighPriority_icon.png"),
                "Medium": get_image_path("MediumPriority_icon.png"),
                "Low": get_image_path("LowPriority_icon.png")
            }
            
            # Set teks button
            button.setText(text if text != "None" else "Priority")
            
            # Set ikon sesuai prioritas yang dipilih
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(priority_icons[text]), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            button.setIcon(icon)
            button.setIconSize(QtCore.QSize(24, 24))
            
        elif button == self.Reminder:
            button.setText(text if text != "None" else "Reminder")

    def validate_input(self):
        """Validasi input untuk mengaktifkan/menonaktifkan tombol Add Task."""
        self.AddTask.setEnabled(bool(self.TaskName.text().strip()))

   
    def clear_inputs(self):
        """Hapus isi input."""
        self.TaskName.clear()
        self.DescTask.clear()
        self.StartTime.setText("Start time")
        self.Deadline.setText("Deadline")
        self.Priority.setText("Priority")
        self.Reminder.setText("Reminder")
        self.AddTask.setEnabled(False)
        self.hide_all_dropdowns()

    def cancel_toggle(self):
        """Toggle visibility of the widget dan clear inputs."""
        self.clear_inputs()
        # Dapatkan parent dialog dan tutup
        parent_dialog = self.parent()
        if parent_dialog and isinstance(parent_dialog, QDialog):
            parent_dialog.reject()
        else:
            self.hide()

    def show_datetime_dialog(self, button):
        """Menampilkan dialog untuk memilih tanggal dan waktu."""
        title = "Select Start Time" if button == self.StartTime else "Select Deadline"
        is_start_time = button == self.StartTime
        
        # Dapatkan nilai deadline atau start time yang sudah dipilih
        current_datetime = QDateTime.currentDateTime()
        default_time = f"{current_datetime.date().toString('yyyy-MM-dd')} {current_datetime.time().toString('HH:mm')}"
        
        dialog = DateTimeDialog(self, title, is_start_time, default_time)
        if dialog.exec_():
            selected_datetime = dialog.get_datetime()
            button.setText(selected_datetime)
            
            # Validasi deadline setelah dipilih
            if not is_start_time:
                if not self.validate_deadline():
                    button.setText("Deadline")
        else:
            # Jika dialog dibatalkan, kembalikan ke teks default
            if is_start_time:
                button.setText("Start time")
            else:
                button.setText("Deadline")

    def validate_start_time(self):
        """Validasi start time terhadap deadline yang sudah dipilih."""
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
        """Validasi deadline terhadap start time yang sudah dipilih."""
        if self.Deadline.text() in ["Deadline", ""]:
            return True
        
        # Jika start time tidak diisi, gunakan waktu saat ini
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

    def set_task_data(self, task_data):
        """Set task data to form fields."""
        if task_data:
            self.TaskName.setText(task_data.get("name", ""))
            self.DescTask.setText(task_data.get("description", ""))
            self.StartTime.setText(task_data.get("start_time", "Start time"))
            self.Deadline.setText(task_data.get("deadline", "Deadline"))
            
            # Handle priority and reminder with proper defaults
            priority = task_data.get("priority", "None")
            reminder = task_data.get("reminder", "None")
            
            # Set button text based on values
            self.Priority.setText(priority if priority != "None" else "Priority")
            self.Reminder.setText(reminder if reminder != "None" else "Reminder")
            
            # Enable Add Task button if name is not empty
            self.AddTask.setEnabled(bool(task_data.get("name", "").strip()))
