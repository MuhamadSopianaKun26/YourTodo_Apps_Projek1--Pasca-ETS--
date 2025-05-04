from PyQt5.QtWidgets import QWidget, QComboBox, QHBoxLayout
from PyQt5.QtCore import Qt

class TaskFilter:
    def __init__(self):
        self.filter_options = {
            "All Tasks": lambda task: True,
            "High Priority": lambda task: task.get("priority", "") == "High",
            "Medium Priority": lambda task: task.get("priority", "") == "Medium",
            "Low Priority": lambda task: task.get("priority", "") == "Low",
            "Completed": lambda task: "done" in task.get("status", "").lower(),
            "Pending": lambda task: task.get("status", "") == "due"
        }
        self.filter_combo = None

    def setup_filter_ui(self):
        """Set up the filter UI components including combo box."""
        filter_container = QWidget()
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(5)
        
        # Create and configure filter combo box
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
        filter_layout.addWidget(self.filter_combo)
        
        return filter_container

    def get_current_filter(self):
        """Get the currently selected filter text.
        
        Returns:
            str: The current filter text or "All Tasks" if no filter is selected
        """
        return self.filter_combo.currentText() if self.filter_combo else "All Tasks"

    def filter_tasks(self, task_list_layout, filter_text):
        """
        Filter tasks based on selected filter option.
        
        Args:
            task_list_layout: The QVBoxLayout containing task widgets
            filter_text: Selected filter option from combo box
        """
        if not task_list_layout:
            return
            
        # Get the filter function based on selected text
        filter_func = self.filter_options.get(filter_text, lambda task: True)
        
        for i in range(task_list_layout.count()):
            widget = task_list_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'task_data'):
                try:
                    task_data = widget.task_data
                    # Apply filter and set visibility
                    widget.setVisible(filter_func(task_data))
                except Exception as e:
                    print(f"Error filtering task: {e}")
                    # Show widget if there's an error
                    widget.setVisible(True)