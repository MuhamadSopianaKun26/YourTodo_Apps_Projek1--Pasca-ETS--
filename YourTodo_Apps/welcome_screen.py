from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from path_utils import get_image_path

class WelcomeScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        # Create and set up the image label
        self.image_label = QLabel()
        pixmap = QPixmap(get_image_path("WellcomeScreen.png.jpg"))
        
        # Scale the image to fit the window while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(1100, 650, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        # Set up the layout with no margins
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.image_label)
        
        # Set the layout
        self.setLayout(layout)
        
        # Set window size to match the scaled image dimensions
        self.setFixedSize(scaled_pixmap.width(), scaled_pixmap.height())
        
        # Set window flags to make it borderless
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Center the window on screen
        self.center()
        
    def center(self):
        # Get the screen geometry
        screen = self.screen().geometry()
        # Calculate center position
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        # Move window to center
        self.move(x, y) 