from PyQt5.QtWidgets import QWidget

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