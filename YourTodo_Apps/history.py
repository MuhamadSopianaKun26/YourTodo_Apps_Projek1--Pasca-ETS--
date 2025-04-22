from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDateEdit, QPushButton, QListWidget, QFileDialog, 
    QMessageBox, QStackedWidget, QSizePolicy, QListWidgetItem
)
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from datetime import datetime, timedelta
from matplotlib.backends.backend_pdf import PdfPages
from path_utils import get_database_path
import re




class HistoryManager:
    @staticmethod
    def load_history(username, start_time, deadline, status_filter="all"):
        done = {}
        failed = {}
        entries = []
        
        history_file = get_database_path("history.txt")
        try:
            with open(history_file, "r") as f:
                for line in f:
                    parts = line.strip().split(" | ")
                    if len(parts) < 7:
                        continue

                    # Handle both 7-field and 9-field formats
                    if len(parts) >= 9:
                        # 9-field format: task, description, start_time, deadline, priority, reminder, status, schedule, entry_username
                        task, description, start_time, deadline, priority, reminder, status, schedule, entry_username = parts[:9]
                    else:
                        # 7-field format: task, description, start_time, deadline, priority, status, entry_username
                        task, description, start_time, deadline, priority, status, entry_username = parts[:7]
                        reminder = ""
                        schedule = ""
                    
                    # Filter by username first
                    if entry_username != username:
                        continue
                    
                    # Extract completion date from status
                    if "on" in status:
                        # Extract the completion date by splitting on "on " and taking the last part
                        # For example: "done - Completed on 2025-04-07" -> "2025-04-07"
                        date_part = status.split("on ")[-1].strip()
                        try:
                            status_date = datetime.strptime(date_part, "%Y-%m-%d").date()
                        except ValueError:
                            # Try alternative date formats if needed
                            continue
                    else:
                        try:
                            status_date = datetime.strptime(status, "%Y-%m-%d").date()
                        except ValueError:
                            continue
                        
                    # NEW STATUS DETECTION
                    status_type = "failed" if "failed" in status.lower() else "done"
                    if status_filter not in ["all", status_type]:
                        continue

                    date_str = status_date.strftime("%Y-%m-%d")
                    if status_type == "failed":
                        failed[date_str] = failed.get(date_str, 0) + 1
                    else:
                        done[date_str] = done.get(date_str, 0) + 1
                    
                    entries.append({
                        'task': task,
                        'description': description,
                        'start_time': start_time,
                        'deadline': deadline,
                        'priority': priority,
                        'reminder': reminder,
                        'status': status,
                        'schedule': schedule,
                        'username': entry_username
                    })
        except FileNotFoundError:
            pass
        print(done)
        print(failed)
        return done, failed, entries
    
class HistoryWidget(QWidget):    
    def __init__(self, username):
        super().__init__()
        self.username = username  # NEW: Store username
        self.initUI()
        self.load_initial_data() 
    
    def load_initial_data(self):
        """Load data with default date range on first open"""
        self.update_date_range()  # Sets default dates
        self.update_display()
    
    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 10)
        main_layout.setSpacing(8)

        # Header remains the same
        header = QHBoxLayout()
        title = QLabel("History")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("margin: 0;")
        header.addWidget(title)
        header.addStretch()
        main_layout.addLayout(header)
        
        # Controls container 
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)

        # Initialize control widgets 
        self.range_combo = QComboBox()
        
        self.status_combo = QComboBox()
        
        self.view_combo = QComboBox()
        
        self.start_date = QDateEdit(calendarPopup=True)
        
        self.end_date = QDateEdit(calendarPopup=True)
        
        self.export_btn = QPushButton("Export PDF")

        # Add controls to layout
        controls_layout.addWidget(self.range_combo)
        controls_layout.addWidget(self.status_combo)
        
        controls_layout.addWidget(QLabel("View:"))
        controls_layout.addWidget(self.view_combo)
        
        controls_layout.addWidget(QLabel("From:"))
        controls_layout.addWidget(self.start_date)
        
        controls_layout.addWidget(QLabel("To:"))
        controls_layout.addWidget(self.end_date)
        
        controls_layout.addWidget(self.export_btn)

        main_layout.addWidget(controls_container)

        # View stack
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Initialize views
        self.figure = Figure(figsize=(10, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        
        # Configure list style
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background: white;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        # Add views to stack
        self.stacked_widget.addWidget(self.canvas)
        self.stacked_widget.addWidget(self.history_list)
        
        main_layout.addWidget(self.stacked_widget, 1)

        # Configure control widgets
        self._configure_controls()

        # Initial setup
        self.update_date_range()
        self.toggle_view()

    def _configure_controls(self):
        # Combo box items
        self.range_combo.addItems(["This Week", "This Month", "This Year", "Custom"])
        
        self.status_combo.addItems(["All", "Done", "Failed"])
        
        self.view_combo.addItems(["Graph View", "Text View"])

        # Style controls
        control_style = "padding: 5px; border-radius: 5px;"
        for widget in [self.range_combo, self.status_combo, 
                      self.view_combo, self.start_date, self.end_date]:
            widget.setStyleSheet(control_style)

        # Export button style
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #00B4D8;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover { background-color: #0096B7; }
        """)

        # Connect signals
        self.range_combo.currentIndexChanged.connect(self.update_date_range)
        self.view_combo.currentIndexChanged.connect(self.toggle_view)
        self.export_btn.clicked.connect(self.export_pdf)
        self.status_combo.currentIndexChanged.connect(self.update_display)
        self.start_date.dateChanged.connect(self.update_display)
        self.end_date.dateChanged.connect(self.update_display)

    def toggle_view(self):
        """Switch between graph and text views"""
        current_index = 0 if self.view_combo.currentText() == "Graph View" else 1
        self.stacked_widget.setCurrentIndex(current_index)
        self.adjustSize()
        self.update_display()

    def update_date_range(self):
        if self.range_combo.currentText() == "Custom":
            self.start_date.setEnabled(True)
            self.end_date.setEnabled(True)
        else:
            today = QDate.currentDate()
            if self.range_combo.currentText() == "This Week":
                # Calculate the start of the week (Monday)
                # In Qt, Monday is 1, Tuesday is 2, etc.
                # We need to go back (dayOfWeek() - 1) days to get to Monday
                days_to_monday = today.dayOfWeek() - 1
                start = today.addDays(-days_to_monday)
                
                # Calculate the end of the week (Sunday)
                # Go forward 6 days from Monday to get to Sunday
                end = start.addDays(6)
            elif self.range_combo.currentText() == "This Month":
                start = QDate(today.year(), today.month(), 1)
                end = today
            else:  # This Year
                start = QDate(today.year(), 1, 1)
                end = today
            
            self.start_date.setDate(start)
            self.end_date.setDate(end)
            self.start_date.setEnabled(False)
            self.end_date.setEnabled(False)
        
        self.update_display()

    def update_display(self):
        
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        
        status_filter = "all" 
        match self.status_combo.currentText():
            case "Done":
                status_filter = "done"
            case "Failed":
                status_filter = "failed"

        # NEW: Pass username to load_history
        if self.view_combo.currentText() == "Graph View":
            self.update_graph(start, end, status_filter)
        else:
            self.update_text_history(start, end, status_filter)

    def update_graph(self, start, end, status_filter):
        # UPDATED: Add username filter
        done, failed, _ = HistoryManager.load_history(
            self.username, start, end, status_filter
        )

        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)

        done_counts = [done.get(d.strftime("%Y-%m-%d"), 0) for d in dates]
        failed_counts = [failed.get(d.strftime("%Y-%m-%d"), 0) for d in dates]

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        bar_width = 0.35  # Width of the bars
        
        if status_filter == "all":
            # Convert dates to numbers for proper bar positioning
            x = [mdates.date2num(d) for d in dates]
            
            # Plot bars side by side
            done_bars = ax.bar([xi - bar_width/2 for xi in x], done_counts, 
                             bar_width, label='Done', color='#4CAF50')
            failed_bars = ax.bar([xi + bar_width/2 for xi in x], failed_counts, 
                                bar_width, label='Failed', color='#FF4444')
            
            # Add value labels on top of bars
            for bars in [done_bars, failed_bars]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:  # Only show label if there's a value
                        ax.text(bar.get_x() + bar.get_width()/2, height,
                               f'{int(height)}',
                               ha='center', va='bottom')
        elif status_filter == "done":
            bars = ax.bar(dates, done_counts, color='#4CAF50')
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, height,
                           f'{int(height)}',
                           ha='center', va='bottom')
        else:
            bars = ax.bar(dates, failed_counts, color='#FF4444')
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, height,
                           f'{int(height)}',
                           ha='center', va='bottom')

        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.set_ylim(bottom=0)
        if status_filter == "all":
            ax.legend()
        self.figure.autofmt_xdate()
        self.canvas.draw()

    def update_text_history(self, start, end, status_filter):
        # Load history with the correct date range
        _, _, entries = HistoryManager.load_history(
            self.username, start, end, status_filter
        )
        self.history_list.clear()

        # Style the QListWidget itself
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;  /* Light gray background */
                border-radius: 8px;
                padding: 8px;
            }
            QListWidget::item {
                background-color: white;     /* White background for items */
                border-radius: 4px;
                margin: 2px;
                padding: 8px;
            }
            QListWidget::item:hover {
                background-color: #e8f4f8;   /* Light blue on hover */
            }
        """)

        # Add a separator item at the beginning
        self.history_list.addItem("")
        
        # Filter entries by date range
        filtered_entries = []
        for entry in entries:
            status_date_str = None
            if "on" in entry['status']:
                status_date_str = entry['status'].split("on ")[-1].strip()
            else:
                status_date_str = entry['status'].strip()
            
            try:
                # Parse the date
                status_date = datetime.strptime(status_date_str, "%Y-%m-%d").date()
                
                # Check if the date is within the selected range
                if start <= status_date <= end:
                    filtered_entries.append(entry)
            except ValueError:
                # Skip entries with invalid date formats
                continue
        
        # Display filtered entries
        for entry in filtered_entries:
            status = "🔴 Failed" if "failed" in entry['status'].lower() else "🟢 Done"
            text = (
                f"Task: {entry['task']}\n"
                f"Description: {entry['description']}\n"
                f"Start: {entry['start_time']} | Deadline: {entry['deadline']}\n"
                f"Priority: {entry['priority']} | Status: {status}"
            )
            item = QListWidgetItem(text)
            self.history_list.addItem(item)
            # Add a separator item after each task
            self.history_list.addItem("")

    def export_pdf(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "", "PDF Files (*.pdf)", options=options
        )
        
        if filename:
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            try:
                with PdfPages(filename) as pdf:
                    pdf.savefig(self.figure)
                QMessageBox.information(self, "Success", "PDF exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
    
