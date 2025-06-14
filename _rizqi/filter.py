# filter.py (complete with all comments preserved and new filters)
from PyQt5.QtWidgets import QWidget, QComboBox, QHBoxLayout, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, QDate, QDateTime

class TaskFilter:
    def __init__(self):
        self.filter_options = {
            "All Tasks": lambda task: True,
            "High Priority": lambda task: task.get("priority", "") == "High",
            "Medium Priority": lambda task: task.get("priority", "") == "Medium",
            "Low Priority": lambda task: task.get("priority", "") == "Low",
            "Completed": lambda task: "done" in task.get("status", "").lower(),
            "Pending": lambda task: task.get("status", "") == "due",
            "Failed": lambda task: "failed" in task.get("status", "").lower(),
            "Scheduled": lambda task: task.get("schedule", "None").lower() != "none"
        }
        self.filter_combo = None
        self.active_filters = {"All Tasks"}  # Set to store active filters

    def setup_filter_ui(self):
        """Set up the filter UI components including combo box and quick filter buttons."""
        filter_container = QWidget()
        main_filter_layout = QVBoxLayout(filter_container)
        main_filter_layout.setContentsMargins(0, 0, 0, 0)
        main_filter_layout.setSpacing(10)

        # Combo Box for main filters
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(self.filter_options.keys())
        self.filter_combo.setStyleSheet(
            """
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 15px;
                min-width: 150px;
            }
            """
        )
        main_filter_layout.addWidget(self.filter_combo)

        # Quick Filter Buttons
        quick_filter_layout = QHBoxLayout()
        quick_filter_layout.setContentsMargins(0, 0, 0, 0)
        quick_filter_layout.setSpacing(5)

        self.btn_all = self._create_quick_filter_button("All Tasks")
        self.btn_completed = self._create_quick_filter_button("Completed")
        self.btn_high_priority = self._create_quick_filter_button("High Priority")
        self.btn_failed = self._create_quick_filter_button("Failed")

        quick_filter_layout.addWidget(self.btn_all)
        quick_filter_layout.addWidget(self.btn_completed)
        quick_filter_layout.addWidget(self.btn_high_priority)
        quick_filter_layout.addWidget(self.btn_failed)
        quick_filter_layout.addStretch()

        main_filter_layout.addLayout(quick_filter_layout)

        return filter_container

    def _create_quick_filter_button(self, text):
        btn = QPushButton(text)
        btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #00B4D8;
                color: white;
                border: 1px solid #00B4D8;
            }
            """
        )
        btn.setCheckable(True)  # Make button checkable for active state
        return btn

    def get_current_filter(self):
        """Get the currently selected filter text from the combo box."""
        return self.filter_combo.currentText() if self.filter_combo else "All Tasks"

    def set_combo_box_filter(self, filter_text):
        """Set the combo box to a specific filter text."""
        if self.filter_combo:
            index = self.filter_combo.findText(filter_text)
            if index >= 0:
                self.filter_combo.setCurrentIndex(index)

    def filter_tasks(self, task_list_layout, selected_combo_filter=None):
        """
        Filter tasks based on active filters (combo box and quick buttons).
        
        Args:
            task_list_layout: The QVBoxLayout containing task widgets
            selected_combo_filter: The filter selected from the combo box, or None if triggered by quick buttons
        """
        if not task_list_layout:
            return

        # If combo box selection changed, update active filters
        if selected_combo_filter:
            self.active_filters.clear()
            self.active_filters.add(selected_combo_filter)
            # Update button states to match combo box selection
            self.btn_all.setChecked(selected_combo_filter == "All Tasks")
            self.btn_completed.setChecked(selected_combo_filter == "Completed")
            self.btn_high_priority.setChecked(selected_combo_filter == "High Priority")
            self.btn_failed.setChecked(selected_combo_filter == "Failed")
        else:
            # Update active_filters based on button states
            self.active_filters.clear()
            if self.btn_all.isChecked(): 
                self.active_filters.add("All Tasks")
            if self.btn_completed.isChecked(): 
                self.active_filters.add("Completed")
            if self.btn_high_priority.isChecked(): 
                self.active_filters.add("High Priority")
            if self.btn_failed.isChecked(): 
                self.active_filters.add("Failed")

            # If no filters are selected, default to "All Tasks"
            if not self.active_filters:
                self.active_filters.add("All Tasks")
                self.btn_all.setChecked(True)

        # Combine filter functions
        combined_filter_func = self._combine_filters(list(self.active_filters))
        
        for i in range(task_list_layout.count()):
            widget = task_list_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'task_data'):
                try:
                    task_data = widget.task_data
                    widget.setVisible(combined_filter_func(task_data))
                except Exception as e:
                    print(f"Error filtering task: {e}")
                    widget.setVisible(True)  # Show widget if there's an error

    def _combine_filters(self, filter_texts):
        """Combines multiple filter functions with OR logic."""
        def combined_func(task):
            # If "All Tasks" is the only active filter, just return True
            if "All Tasks" in filter_texts and len(filter_texts) == 1:
                return True
            
            # If "All Tasks" is present with other filters, remove it to avoid conflict
            effective_filters = [f for f in filter_texts if f != "All Tasks"]
            if not effective_filters:  # If only "All Tasks" was effectively selected
                return True

            # Check if task matches any of the selected filters (OR logic)
            for filter_text in effective_filters:
                filter_func = self.filter_options.get(filter_text)
                if filter_func and filter_func(task):
                    return True
            return False
        return combined_func

    def get_active_filters_state(self):
        """Get the state of active filters for saving."""
        active_state = {
            "combo_box_text": self.filter_combo.currentText() if self.filter_combo else "All Tasks",
            "quick_buttons": {
                "All Tasks": self.btn_all.isChecked(),
                "Completed": self.btn_completed.isChecked(),
                "High Priority": self.btn_high_priority.isChecked(),
                "Failed": self.btn_failed.isChecked()
            }
        }
        return active_state

    def set_active_filters_state(self, state):
        """Set the state of active filters from loaded settings."""
        if not state:
            return

        # Set combo box
        combo_text = state.get("combo_box_text", "All Tasks")
        self.set_combo_box_filter(combo_text)

        # Set quick buttons
        quick_buttons_state = state.get("quick_buttons", {})
        if self.btn_all: self.btn_all.setChecked(quick_buttons_state.get("All Tasks", False))
        if self.btn_completed: self.btn_completed.setChecked(quick_buttons_state.get("Completed", False))
        if self.btn_high_priority: self.btn_high_priority.setChecked(quick_buttons_state.get("High Priority", False))
        if self.btn_failed: self.btn_failed.setChecked(quick_buttons_state.get("Failed", False))