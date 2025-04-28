from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
import hashlib, re
from path_utils import get_image_path, get_database_path


class LoginDialog(QDialog):
    """
    A dialog window for user authentication that provides login functionality
    and navigation to registration.
    """

    def __init__(self):
        super().__init__()
        self.username = ""
        self.setWindowTitle("Login")
        self.setFixedSize(1100, 650)
        self._setup_styles()
        self.initUI()

    def _setup_styles(self):
        """Configure the styling for the login dialog components."""
        self.setStyleSheet(
            """
            QDialog {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #E0F7FA,
                    stop: 1 #B2EBF2
                );
            }
            QLabel {
                color: #333;
                font-size: 18px;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                background: white;
                font-size: 18px;
                min-width: 300px;
            }
            QPushButton#loginBtn {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 18px;
                min-width: 300px;
            }
            QPushButton#loginBtn:hover {
                background-color: #1976D2;
            }
            QPushButton#registerBtn {
                background: none;
                border: none;
                color: #2196F3;
                text-decoration: underline;
                font-size: 18px;
            }
            QPushButton#registerBtn:hover {
                color: #1976D2;
            }
        """
        )

    def initUI(self):
        """Initialize and setup the user interface components."""
        main_layout = QHBoxLayout()
        main_layout.addWidget(self._create_login_form())
        main_layout.addWidget(self._create_illustration())
        self.setLayout(main_layout)

    def _create_login_form(self):
        """Create and return the login form widget."""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(50, 50, 50, 50)
        left_layout.setSpacing(15)

        title = QLabel("Login")
        title.setFont(QFont("Arial", 48, QFont.Bold))
        title.setStyleSheet("color: #333; font-size: 48px;")

        self.email = QLineEdit()
        self.email.setPlaceholderText("Enter Your Email...")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter Your Password...")
        self.password.setEchoMode(QLineEdit.Password)

        login_btn = QPushButton("Login")
        login_btn.setObjectName("loginBtn")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self.login)

        left_layout.addWidget(title)
        left_layout.addSpacing(20)
        left_layout.addWidget(QLabel("Email"))
        left_layout.addWidget(self.email)
        left_layout.addWidget(QLabel("Password"))
        left_layout.addWidget(self.password)
        left_layout.addSpacing(10)
        left_layout.addWidget(login_btn)
        left_layout.addWidget(self._create_register_link())
        left_layout.addStretch()
        left_layout.addWidget(self._create_logo())

        left_widget.setLayout(left_layout)
        return left_widget

    def _create_register_link(self):
        """Create and return the registration link widget."""
        register_container = QWidget()
        register_layout = QHBoxLayout()

        register_label = QLabel("Don't have an account?")
        register_label.setStyleSheet("color: #666;")

        register_btn = QPushButton("Sign up")
        register_btn.setObjectName("registerBtn")
        register_btn.setCursor(Qt.PointingHandCursor)
        register_btn.clicked.connect(self.register)

        register_layout.addWidget(register_label)
        register_layout.addWidget(register_btn)
        register_layout.setAlignment(Qt.AlignLeft)
        register_container.setLayout(register_layout)
        return register_container

    def _create_logo(self):
        """Create and return the logo widget."""
        logo_label = QLabel()
        logo_pixmap = QPixmap(get_image_path("logo.png"))
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaled(
                250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
        return logo_label

    def _create_illustration(self):
        """Create and return the illustration widget."""
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        illustration_label = QLabel()
        illustration_pixmap = QPixmap(get_image_path("auth_illustration.png"))
        if not illustration_pixmap.isNull():
            illustration_pixmap = illustration_pixmap.scaled(
                500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            illustration_label.setPixmap(illustration_pixmap)
            illustration_label.setAlignment(Qt.AlignCenter)

        right_layout.addWidget(illustration_label)
        right_widget.setLayout(right_layout)
        return right_widget

    def _hash_password(self, password):
        """Hash the password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _load_users(self):
        """Load user credentials from the users.txt file."""
        users = {}
        try:
            users_file = get_database_path("users.txt")
            with open(users_file, "r") as file:
                for line in file:
                    parts = line.strip().split(" | ")
                    if len(parts) == 3:
                        email, username, password_hash = parts
                        users[email] =(username, password_hash)
        except FileNotFoundError:
            with open(users_file, "w", encoding="utf-8") as file:
                file.write("")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error loading users: {str(e)}")
            return {}
        return users

    def login(self):
        """Handle the login process and validation."""
        email = self.email.text().strip()
        password = self.password.text()

        if not email or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        users = self._load_users()
        password_hash = self._hash_password(password)

        if email in users: 
            stored_username, stored_hash = users[email]
            if stored_hash == password_hash:
                self.username = stored_username
                self.accept()
                return
        else:
            QMessageBox.warning(self, "Error", "Invalid email or password")

    def register(self):
        """Open the registration dialog."""
        dialog = RegistrationDialog(self)
        dialog.exec_()


class RegistrationDialog(QDialog):
    """
    A dialog window for new user registration that provides form validation
    and account creation functionality.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register")
        self.setFixedSize(1100, 750)
        self._setup_styles()
        self.initUI()

    def _setup_styles(self):
        """Configure the styling for the registration dialog components."""
        self.setStyleSheet(
            """
            QDialog {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #E0F7FA,
                    stop: 1 #B2EBF2
                );
            }
            QLabel {
                color: #333;
                font-size: 18px;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                background: white;
                font-size: 18px;
                min-width: 300px;
            }
            QPushButton#loginBtn {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 18px;
                min-width: 300px;
            }
            QPushButton#loginBtn:hover {
                background-color: #1976D2;
            }
            QPushButton#registerBtn {
                background: none;
                border: none;
                color: #2196F3;
                text-decoration: underline;
                font-size: 18px;
            }
            QPushButton#registerBtn:hover {
                color: #1976D2;
            }
        """
        )

    def initUI(self):
        """Initialize and setup the user interface components."""
        main_layout = QHBoxLayout()
        main_layout.addWidget(self._create_registration_form())
        main_layout.addWidget(self._create_illustration())
        self.setLayout(main_layout)

    def _create_registration_form(self):
        """Create and return the registration form widget."""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(50, 50, 50, 50)
        left_layout.setSpacing(15)

        title = QLabel("Register")
        title.setFont(QFont("Arial", 48, QFont.Bold))
        title.setStyleSheet("color: #333; font-size: 48px;")

        self.email = QLineEdit()
        self.email.setPlaceholderText("Enter Your Email...")

        self.username = QLineEdit()
        self.username.setPlaceholderText("Enter Your Username...")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter Your Password...")
        self.password.setEchoMode(QLineEdit.Password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm Your Password...")
        self.confirm_password.setEchoMode(QLineEdit.Password)

        register_btn = QPushButton("Register")
        register_btn.setObjectName("loginBtn")
        register_btn.setCursor(Qt.PointingHandCursor)
        register_btn.clicked.connect(self.register)

        left_layout.addWidget(title)
        left_layout.addSpacing(20)
        left_layout.addWidget(QLabel("Email"))
        left_layout.addWidget(self.email)
        left_layout.addWidget(QLabel("Username"))
        left_layout.addWidget(self.username)
        left_layout.addWidget(QLabel("Password"))
        left_layout.addWidget(self.password)
        left_layout.addWidget(QLabel("Confirm Password"))
        left_layout.addWidget(self.confirm_password)
        left_layout.addSpacing(10)
        left_layout.addWidget(register_btn)
        left_layout.addWidget(self._create_login_link())
        left_layout.addStretch()
        left_layout.addWidget(self._create_logo())

        left_widget.setLayout(left_layout)
        return left_widget

    def _create_login_link(self):
        """Create and return the login link widget."""
        login_container = QWidget()
        login_layout = QHBoxLayout()

        login_label = QLabel("Already have an account?")
        login_label.setStyleSheet("color: #666;")

        login_btn = QPushButton("Login")
        login_btn.setObjectName("registerBtn")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self.accept)

        login_layout.addWidget(login_label)
        login_layout.addWidget(login_btn)
        login_layout.setAlignment(Qt.AlignLeft)
        login_container.setLayout(login_layout)
        return login_container

    def _create_logo(self):
        """Create and return the logo widget."""
        logo_label = QLabel()
        logo_pixmap = QPixmap(get_image_path("logo.png"))
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaled(
                250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
        return logo_label

    def _create_illustration(self):
        """Create and return the illustration widget."""
        right_widget = QWidget()
        right_layout = QVBoxLayout()

        illustration_label = QLabel()
        illustration_pixmap = QPixmap(get_image_path("auth_illustration.png"))
        if not illustration_pixmap.isNull():
            illustration_pixmap = illustration_pixmap.scaled(
                500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            illustration_label.setPixmap(illustration_pixmap)
            illustration_label.setAlignment(Qt.AlignCenter)

        right_layout.addWidget(illustration_label)
        right_widget.setLayout(right_layout)
        return right_widget

    def _hash_password(self, password):
        """Hash the password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self):
        """Handle the registration process with validation."""
        email = self.email.text().strip()
        username = self.username.text().strip()
        password = self.password.text()
        confirm_password = self.confirm_password.text()

        if not email or not username or not password or not confirm_password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return
        
        if len(email) < 6 or len(email) > 30:
            QMessageBox.warning(self, "Error", "Email must be between 6 and 30 character long")
            return
        
        if not re.search(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            QMessageBox.warning(self, "Error", "Email Format not valid")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        if len(password) < 8:
            QMessageBox.warning(
                self, "Error", "Password must be at least 8 characters long"
            )
            return
        
        if not re.search(r'[A-Z]', password):
            QMessageBox.warning(
                self, "Error", "Password must containt an uppercase letter"
            )
            return

        if not re.search(r'[a-z]', password):
            QMessageBox.warning(
                self, "Error", "Password must containt a lowercase letter"
            )
            return
        
        if not re.search(r'[0-9]', password):
            QMessageBox.warning(
                self, "Error", "Password must containt a number"
            )
            return

        users_file = get_database_path("users.txt")

        # Check for existing username
        try:
            with open(users_file, "r", encoding="utf-8") as file:
                for line in file:
                    parts = line.strip().split(" | ")
                    if len(parts) == 3:
                        existing_email = line.strip().split(" | ")[0]
                        if email == existing_email:
                            QMessageBox.warning(self, "Error", "Email already exists")
                            return
                        existing_username = line.strip().split(" | ")[1]
                        if username == existing_username:
                            QMessageBox.warning(self, "Error", "Username already exists")
                            return
        except FileNotFoundError:
            pass

        # Create new user account
        password_hash = self._hash_password(password)
        try:
            with open(users_file, "a") as file:
                file.write(f"{email} | {username} | {password_hash}\n")
            QMessageBox.information(
                self, "Success", "Registration successful! You can now login."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error registering user: {e}")
