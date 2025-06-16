from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QMessageBox,
    QStackedWidget,
    QComboBox, 
)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QSettings, QDate
from PyQt5.QtGui import QFont, QIcon
import json

from _sopian.main_components import TaskItemWidget, LoadingWidget
from _sopian.repeatedTask import RepeatedTaskManager
from _sopian.path_utils import get_image_path, get_database_path
from _rizqi.filter import TaskFilter
from _darrel.create import TodoCreator


class TaskManager:
    def __init__(self, main_app):
        self.main_app = main_app
        self.task_list_layout = None
        self.content_stack = None
        self.loading_widget = None
        self.task_count_label = None
        self.task_filter = TaskFilter()
        self.settings = QSettings("SopianApp", "TaskFilterSettings") # For saving settings
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
        self.filter_button_style = """
            QPushButton {
                background-color: #00B4D8;
                border: none;
                border-radius: 15px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #0096B7;
            }
        """
        self.initUI()

    def initUI(self):
        self.setupTasksWidget()

    def setupTasksWidget(self):
        """Set up the Tasks section widget with task list and action buttons."""
        self.tasks_widget = QWidget()
        layout = QVBoxLayout(self.tasks_widget)

        header_layout = QHBoxLayout()
        self.task_count_label = QLabel("Tasks: 0")
        self.task_count_label.setStyleSheet(
            """
            QLabel {
                color: #333;
                font-size: 24px;
                font-weight: bold;
            }
        """
        )
        header_layout.addWidget(self.task_count_label)
        header_layout.addStretch()

        # Integrate TaskFilter UI
        filter_ui_container = self.task_filter.setup_filter_ui()
        header_layout.addWidget(filter_ui_container)
        header_layout.addStretch()

        # Connect filter combo box
        self.task_filter.filter_combo.currentIndexChanged.connect(self._on_filter_combo_changed)
        
        # Connect quick filter buttons using lambda to pass the button object
        self.task_filter.btn_all.clicked.connect(lambda: self._on_quick_filter_button_clicked(self.task_filter.btn_all))
        self.task_filter.btn_completed.clicked.connect(lambda: self._on_quick_filter_button_clicked(self.task_filter.btn_completed))
        self.task_filter.btn_high_priority.clicked.connect(lambda: self._on_quick_filter_button_clicked(self.task_filter.btn_high_priority))
        self.task_filter.btn_failed.clicked.connect(lambda: self._on_quick_filter_button_clicked(self.task_filter.btn_failed))

        add_btn = self._createActionButton("Add Task", get_image_path("add.png"))
        add_btn.clicked.connect(self.addTask)
        header_layout.addWidget(add_btn)

        clear_btn = self._createActionButton("Clear All", get_image_path("clear.png"))
        clear_btn.clicked.connect(self.clearAllTasks)
        header_layout.addWidget(clear_btn)

        refresh_btn = self._createActionButton("Refresh", get_image_path("refresh.png"))
        refresh_btn.clicked.connect(self.refreshTasks)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)

        scroll = self._setupTaskList()
        self.loading_widget = LoadingWidget()

        self.content_stack.addWidget(scroll)
        self.content_stack.addWidget(self.loading_widget)
        self.content_stack.setCurrentWidget(scroll)

        self.load_filter_settings() # Load filter settings on startup

        return self.tasks_widget

    def _on_filter_combo_changed(self):
        """Handle change in the main filter combo box."""
        selected_text = self.task_filter.filter_combo.currentText()
        # Clear all quick filter buttons when combo box selection changes
        for btn in [self.task_filter.btn_all, 
                   self.task_filter.btn_completed,
                   self.task_filter.btn_high_priority,
                   self.task_filter.btn_failed]:
            btn.setChecked(False)
        
        # Apply the selected filter from combo box
        self.applyFilters(selected_text=selected_text)
        self.save_filter_settings()

    def _on_quick_filter_button_clicked(self, clicked_button):
        """Handle clicks on quick filter buttons, allowing multiple selections."""
        # Get the current checked state of the button being clicked
        is_checked = clicked_button.isChecked()

        # Special handling for "All Tasks" button
        if clicked_button == self.task_filter.btn_all:
            if is_checked:
                # Uncheck all other buttons when "All Tasks" is checked
                for btn in [self.task_filter.btn_completed, 
                          self.task_filter.btn_high_priority,
                          self.task_filter.btn_failed]:
                    btn.setChecked(False)
                # Update combo box to show "All Tasks"
                self.task_filter.set_combo_box_filter("All Tasks")
            else:
                # Prevent unchecking "All Tasks" if no other filters are selected
                if not any(btn.isChecked() for btn in [self.task_filter.btn_completed,
                                                     self.task_filter.btn_high_priority,
                                                     self.task_filter.btn_failed]):
                    clicked_button.setChecked(True)
        else:
            # For other buttons, uncheck "All Tasks" if this button is being checked
            if is_checked:
                self.task_filter.btn_all.setChecked(False)

        # Update combo box to show "Multiple Filters" when appropriate
        active_buttons = [btn for btn in [self.task_filter.btn_completed,
                                       self.task_filter.btn_high_priority,
                                       self.task_filter.btn_failed]
                        if btn.isChecked()]
        
        if len(active_buttons) == 1:
            self.task_filter.set_combo_box_filter(active_buttons[0].text())
        elif len(active_buttons) > 1:
            self.task_filter.set_combo_box_filter("Multiple Filters")
        elif self.task_filter.btn_all.isChecked():
            self.task_filter.set_combo_box_filter("All Tasks")

        self.applyFilters()
        self.save_filter_settings()

    def applyFilters(self, selected_text=None):
        """Apply filters using the TaskFilter class and update the task count to reflect visible tasks."""
        self.task_filter.filter_tasks(self.task_list_layout, selected_text)
        # Count visible tasks after filtering
        visible_count = 0
        if self.task_list_layout:
            for i in range(self.task_list_layout.count()):
                widget = self.task_list_layout.itemAt(i).widget()
                if widget and widget.isVisible():
                    visible_count += 1
        if self.task_count_label:
            self.task_count_label.setText(f"Tasks: {visible_count}")
        
        # Save filter settings after applying
        self.save_filter_settings()

    def load_filter_settings(self):
        """Load filter settings from QSettings."""
        if self.main_app.current_user:
            settings_key = f"filter_settings/{self.main_app.current_user}"
            loaded_state = self.settings.value(settings_key)
            if loaded_state:
                # QSettings might return string for complex objects, convert back from JSON string if needed
                if isinstance(loaded_state, str):
                    try:
                        loaded_state = json.loads(loaded_state)
                    except json.JSONDecodeError:
                        loaded_state = None 

                if loaded_state:
                    self.task_filter.set_active_filters_state(loaded_state)
                    # Apply filters based on actual button states after loading
                    self.applyFilters() 
            else:
                # If no settings are found, ensure "All Tasks" is selected and applied
                self.task_filter.set_combo_box_filter("All Tasks")
                self.task_filter.btn_all.setChecked(True)
                # Uncheck all other specific buttons to ensure clean state
                for btn in [self.task_filter.btn_completed, self.task_filter.btn_high_priority, 
                            self.task_filter.btn_today]:
                    btn.setChecked(False)
                self.applyFilters()

    def save_filter_settings(self):
        """Save current filter settings to QSettings."""
        if self.main_app.current_user:
            settings_key = f"filter_settings/{self.main_app.current_user}"
            state_to_save = self.task_filter.get_active_filters_state()
            # QSettings can store dict, but for complex nested dicts, JSON string is safer
            self.settings.setValue(settings_key, json.dumps(state_to_save))

    def _createActionButton(self, text, icon_path=None):
        """Create a styled action button with optional icon."""
        btn = QPushButton(text)
        if icon_path:
            btn.setIcon(QIcon(icon_path))
        btn.setStyleSheet(self.action_button_style)
        return btn

    def clearAllTasks(self):
        """Clear all tasks after user confirmation."""
        reply = QMessageBox.question(
            self.main_app,
            "Clear All Tasks",
            "Are you sure you want to clear all tasks?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            if self.task_list_layout:
                while self.task_list_layout.count():
                    item = self.task_list_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

                self.saveTasks()
                self.updateTaskCount()
                self.applyFilters() # Reapply filters after clearing tasks

    def _setupTaskList(self):
        """Create and return a scrollable task list area."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background-color: transparent; }"
        )

        self.task_list_widget = QWidget()
        self.task_list_layout = QVBoxLayout(self.task_list_widget)
        self.task_list_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.task_list_widget)

        return scroll

    def loadTasks(self):
        """Load tasks from file for the current user and update UI."""
        try:
            tasks_data = []
            task_file = get_database_path("tasks.json")

            # Load tasks from tasks.json
            try:
                with open(task_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    for task in data.get("tasks", []):
                        if task["username"] == self.main_app.current_user:
                            tasks_data.append(task)
            except FileNotFoundError:
                with open(task_file, "w", encoding="utf-8") as file:
                    json.dump({"tasks": []}, file, indent=2)
            except json.JSONDecodeError:
                QMessageBox.critical(self.main_app, "Error", "Invalid JSON format in tasks file")
                return

            # Clear existing tasks from UI
            for i in reversed(range(self.task_list_layout.count())):
                widget = self.task_list_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None) # Remove from layout and delete
                    widget.deleteLater() # Ensure widget is properly deleted

            # Add tasks to UI
            for task_data in tasks_data:
                task_widget = TaskItemWidget(task_data, self.main_app)
                self.task_list_layout.addWidget(task_widget)

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error loading tasks: {str(e)}")

        self.applyFilters(selected_text=self.task_filter.get_current_filter()) # Reapply filters after loading tasks
        self.updateTaskCount()

    def addTask(self):
        """Open dialog to create a new task."""
        TodoCreator.add_task(self.main_app, self.saveNewTask)

    def saveNewTask(self, task_data):
        """Save new task and update UI."""
        try:
            task_widget = TaskItemWidget(task_data, self.main_app)
            self.task_list_layout.addWidget(task_widget)

            # Save task to tasks.json
            self.saveTasks()

            # If task has a schedule, save it to scheduled_tasks.json
            schedule = task_data.get("schedule", "None")
            if schedule and schedule.lower() != "none":
                schedule_file = get_database_path("scheduled_tasks.json")
                try:
                    # Read existing scheduled tasks
                    try:
                        with open(schedule_file, "r", encoding="utf-8") as file:
                            data = json.load(file)
                            scheduled_tasks = data.get("scheduled_tasks", [])
                    except (FileNotFoundError, json.JSONDecodeError):
                        scheduled_tasks = []

                    # Add new scheduled task
                    # Ensure start_time is present for last_run_date if not already
                    if "start_time" in task_data:
                        task_data["last_run_date"] = QDateTime.fromString(task_data["start_time"], "yyyy-MM-dd HH:mm:ss").date().toString("yyyy-MM-dd")
                    else: # Fallback if start_time is missing, though it should be handled in TodoCreator
                        task_data["last_run_date"] = QDate.currentDate().toString("yyyy-MM-dd")

                    scheduled_tasks.append(task_data)

                    # Save updated scheduled tasks
                    with open(schedule_file, "w", encoding="utf-8") as file:
                        json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

                except Exception as e:
                    QMessageBox.critical(
                        None, "Error", f"Error saving scheduled task: {str(e)}"
                    )
            
            self.applyFilters() # Reapply filters after adding a new task

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error adding task: {str(e)}")

    def saveTasks(self):
        """Save all tasks to file."""
        try:
            tasks_data = []
            task_file = get_database_path("tasks.json")

            # Get existing tasks for other users
            try:
                with open(task_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    tasks_data = [
                        task
                        for task in data.get("tasks", [])
                        if task["username"] != self.main_app.current_user
                    ]
            except FileNotFoundError:
                pass
            except json.JSONDecodeError:
                QMessageBox.critical(self.main_app, "Error", "Invalid JSON format in tasks file")
                return

            # Add current user's tasks
            for i in range(self.task_list_layout.count()):
                widget = self.task_list_layout.itemAt(i).widget()
                if isinstance(widget, TaskItemWidget):
                    tasks_data.append(widget.task_data)

            # Save all tasks
            with open(task_file, "w", encoding="utf-8") as file:
                json.dump({"tasks": tasks_data}, file, indent=2)

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error saving tasks: {str(e)}")

    def updateTaskCount(self):
        """Update the task count display."""
        # This now counts all tasks, not just visible ones, before filtering
        count = self.task_list_layout.count() 
        self.task_count_label.setText(f"Tasks: {count}")

    def refreshTasks(self):
        """Refresh tasks with loading animation and clear the search bar."""
        # Clear the search bar if available
        if hasattr(self.main_app, "header") and hasattr(
            self.main_app.header, "search_bar"
        ):
            self.main_app.header.search_bar.setText("")
        self.content_stack.setCurrentWidget(self.loading_widget)
        QTimer.singleShot(1000, self._performRefresh)

    def _performRefresh(self):
        """Perform the actual refresh operation."""
        # Checking the unAdded scheduled task
        RepeatedTaskManager.checkAndAddScheduledTasks(self)
        # Load tasks first to ensure we have all tasks
        self.loadTasks()
        # Then save to preserve any changes (e.g., from scheduled tasks being added)
        self.saveTasks()
        self.content_stack.setCurrentWidget(self.content_stack.widget(0))
        self.applyFilters(selected_text=self.task_filter.get_current_filter()) # Reapply filters after refresh

    def deleteTask(self, task_widget):
        """Delete a task."""
        try:
            # Remove from UI
            task_widget.setParent(None)
            task_widget.deleteLater() # Ensure proper deletion

            # Save changes to file
            self.saveTasks()

            # If it's a scheduled task, remove from scheduled_tasks.json
            if task_widget.task_data.get("schedule", "None").lower() != "none":
                schedule_file = get_database_path("scheduled_tasks.json")
                try:
                    with open(schedule_file, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        scheduled_tasks = data.get("scheduled_tasks", [])

                    # Remove matching task
                    # Ensure matching based on a unique identifier or a combination
                    scheduled_tasks = [
                        task
                        for task in scheduled_tasks
                        if not (
                            task.get("name") == task_widget.task_data.get("name")
                            and task.get("username") == task_widget.task_data.get("username")
                            and task.get("created_at") == task_widget.task_data.get("created_at") # Use created_at for uniqueness
                        )
                    ]

                    with open(schedule_file, "w", encoding="utf-8") as file:
                        json.dump({"scheduled_tasks": scheduled_tasks}, file, indent=2)

                except Exception as e:
                    QMessageBox.critical(
                        None, "Error", f"Error removing scheduled task: {str(e)}"
                    )
            
            self.applyFilters() # Reapply filters after deleting a task

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error deleting task: {str(e)}")

    def moveToHistory(self, task_widget):
        """Move a completed or failed task to history."""
        try:
            history_file = get_database_path("history.json")

            # Load existing history
            try:
                with open(history_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    history = data.get("history", [])
            except (FileNotFoundError, json.JSONDecodeError):
                history = []

            # Add task to history
            task_widget.task_data["moved_to_history_at"] = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
            history.append(task_widget.task_data)

            # Save updated history
            with open(history_file, "w", encoding="utf-8") as file:
                json.dump({"history": history}, file, indent=2)

            # Delete task from active tasks
            self.deleteTask(task_widget)

        except Exception as e:
            QMessageBox.critical(
                None, "Error", f"Error moving task to history: {str(e)}"
            )

    def filter_tasks_by_query(self, query):
        """Show/hide tasks based on search query (matches name or description, case-insensitive), and update the task count to reflect visible tasks."""
        if not self.task_list_layout:
            return
        query = query.strip().lower()
        
        # Preserve current filter settings while applying search
        temp_active_filters = self.task_filter.active_filters.copy()

        visible_count = 0
        for i in range(self.task_list_layout.count()):
            widget = self.task_list_layout.itemAt(i).widget()
            if not hasattr(widget, "task_data"):
                continue
            name = widget.task_data.get("name", "").lower()
            desc = widget.task_data.get("description", "").lower()

            # Check visibility based on existing filters first
            is_visible_by_filters = self.task_filter._combine_filters(list(temp_active_filters))(widget.task_data)

            if is_visible_by_filters and (not query or query in name or query in desc):
                widget.show()
                visible_count += 1
            else:
                widget.hide()
        
        # Update the task count label to show only visible tasks
        if self.task_count_label:
            self.task_count_label.setText(f"Tasks: {visible_count}")

    def update_text(self, key, new_text):
        """Update text when language changes"""
        # Update task-related text
        if hasattr(self, "add_task_btn"):
            if key == "add_task":
                self.add_task_btn.setText(new_text)

        # Update task item texts
        for i in range(self.task_list_layout.count()):
            widget = self.task_list_layout.itemAt(i).widget()
            if isinstance(widget, TaskItemWidget):
                widget.update_text(key, new_text)

        # Update task count label if it exists
        if hasattr(self, "task_count_label"):
            if key == "tasks":
                count = self.task_list_layout.count() if self.task_list_layout else 0
                self.task_count_label.setText(f"{new_text} ({count})")
