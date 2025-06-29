from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QWidget,
    QAction,
    QInputDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QIcon
import hashlib, re, json
from _sopian.path_utils import get_image_path, get_database_path
from _praditama.otp_verification import OTPVerification, OTPDialog


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
        self._last_login_attempt = False
        self.email.textChanged.connect(self._update_forgotPass_state)
        self.password.textChanged.connect(self._update_forgotPass_state)

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
        self.add_toggle_action(self.password, self)

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
        left_layout.addWidget(self._create_ForgotPass_link())
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
    
    def _create_ForgotPass_link(self):
        """Create and return the Forgot Password link widget."""
        forgotPass_container = QWidget()
        forgotPass_layout = QHBoxLayout()

        forgotPass_label = QLabel("Forgot Your Password?")
        forgotPass_label.setStyleSheet("color: #666;")

        self.forgotPass_btn = QPushButton("Reset Password")
        self.forgotPass_btn.setObjectName("forgotPassBtn")
        self.forgotPass_btn.setCursor(Qt.PointingHandCursor)
        self.forgotPass_btn.clicked.connect(self.ForgotPass)
        self.forgotPass_btn.setEnabled(False)
        self.forgotPass_btn.setStyleSheet("""
            color: #9E9E9E;
            text-decoration: underline;
            background: none;
            border: none;
            font-size: 18px;
        """)

        forgotPass_layout.addWidget(forgotPass_label)
        forgotPass_layout.addWidget(self.forgotPass_btn)
        forgotPass_layout.setAlignment(Qt.AlignLeft)
        forgotPass_container.setLayout(forgotPass_layout)
        return forgotPass_container

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
    
    def _update_forgotPass_state(self):
        """Update the state of the forgot password button based on input fields."""
        email = self.email.text().strip()
        password = self.password.text()
        
        enable_reset = False
        
        # Only check further conditions if we have both email and password
        if email and password:
            users_data = self._load_users()

            if email in users_data:
                stored_hash = users_data[email][1]
                password_hash = self._hash_password(password)
                
                if self._last_login_attempt and stored_hash != password_hash:
                    enable_reset = True
        
        self.forgotPass_btn.setEnabled(enable_reset)
        
        # Update button styling based on state
        if enable_reset:
            self.forgotPass_btn.setStyleSheet("""
                color: #2196F3;
                text-decoration: underline;
                background: none;
                border: none;
                font-size: 18px;
            """)
        else:
            self.forgotPass_btn.setStyleSheet("""
                color: #9E9E9E;
                text-decoration: underline;
                background: none;
                border: none;
                font-size: 18px;
            """)


    def _hash_password(self, password):
        """Hash the password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _load_users(self):
        """Load user credentials from the users.json file."""
        users = {}
        try:
            users_file = get_database_path("users.json")
            with open(users_file, "r") as file:
                data = json.load(file)
                for user in data.get("users", []):
                    users[user["email"]] = (user["username"], user["password_hash"])
        except FileNotFoundError:
            with open(users_file, "w", encoding="utf-8") as file:
                json.dump({"users": []}, file, indent=2)
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
                self._last_login_attempt = False
                self.accept()
                return
            else:
                self._last_login_attempt = True
                QMessageBox.warning(self, "Error", "Password Invalid")
                self._update_forgotPass_state()
        else:
            QMessageBox.warning(self, "Error", "Invalid Email or Email not found!")

    def register(self):
        """Open the registration dialog."""
        dialog = RegistrationDialog(self)
        dialog.exec_()
    
    def ForgotPass(self):
        """Open the Forgot Password Dialog"""
        current_email = self.email.text()
        dialog = ForgotPassDialog(current_email)
        dialog.exec_()

    # update 22 April 2025
    # for toggling password visibility
    # using staticmethod to allow easy access from RegistrationDialog
    @staticmethod
    def add_toggle_action(line_edit, parent):
        # Create toggle action for any QLineEdit
        toggle_action = QAction(parent)
        toggle_action.setIcon(QIcon(get_image_path("eye_closed.png")))
        toggle_action.triggered.connect(
            lambda: LoginDialog.toggle_visibility(line_edit, toggle_action)
        )
        line_edit.addAction(toggle_action, QLineEdit.TrailingPosition)

    @staticmethod
    def toggle_visibility(line_edit, action):
        # Generic method to toggle any QLineEdit's visibility
        if line_edit.echoMode() == QLineEdit.Password:
            line_edit.setEchoMode(QLineEdit.Normal)
            action.setIcon(QIcon(get_image_path("eye_open.png")))
        else:
            line_edit.setEchoMode(QLineEdit.Password)
            action.setIcon(QIcon(get_image_path("eye_closed.png")))


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
        self.otp_verification = OTPVerification()
        self.otp_verified = False  # Placeholder for OTP verification
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
        LoginDialog.add_toggle_action(self.password, self)

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm Your Password...")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        LoginDialog.add_toggle_action(self.confirm_password, self)

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

        if len(email) < 6:
            QMessageBox.warning(
                self, "Error", "Email must be at least 6 character long"
            )
            return

        if not re.search(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
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

        if not re.search(r"[A-Z]", password):
            QMessageBox.warning(
                self, "Error", "Password must containt an uppercase letter"
            )
            return

        if not re.search(r"[a-z]", password):
            QMessageBox.warning(
                self, "Error", "Password must containt a lowercase letter"
            )
            return

        if not re.search(r"[0-9]", password):
            QMessageBox.warning(self, "Error", "Password must containt a number")
            return
        
        if not self.otp_verified:
            self._verify_email_otp()
            return

        users_file = get_database_path("users.json")
        try:
            # Load existing users
            try:
                with open(users_file, "r") as file:
                    data = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {"users": []}

            # Check if email already exists
            if any(user["email"] == email for user in data["users"]):
                QMessageBox.warning(self, "Error", "Email already registered")
                return

            # Add new user
            data["users"].append(
                {
                    "email": email,
                    "username": username,
                    "password_hash": self._hash_password(password),
                }
            )

            # Save updated users
            with open(users_file, "w") as file:
                json.dump(data, file, indent=2)

            QMessageBox.information(self, "Success", "Registration successful!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Registration failed: {str(e)}")
            return
        
    def _verify_email_otp(self):
        """Handle the email OTP verification process."""
        email = self.email.text().strip()
        if not email:
            QMessageBox.warning(self, "Error", "Please enter your email First")
            return
        
        if not re.search(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            QMessageBox.warning(self, "Error", "Invalid email format")
            return
        
        otp_dialog = OTPDialog(self.otp_verification, email, self)
        if otp_dialog.exec_() == QDialog.Accepted:
            self.otp_verified = True
            self.register()

class ForgotPassDialog(QDialog):
    """
    A dialog for user who forgot password and want to change password
    without make a new account
    """

    def __init__(self, email, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reset Password")
        self.setFixedSize(1100, 750)
        self._setup_styles()
        self.current_email = email #Store the email passed from LoginDialog
        self.otp_verification = OTPVerification()
        self.otp_verified = False
        self.initUI()
        self._verify_email_otp()
        
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
                padding: 12px;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                background: white;
                font-size: 18px;
                min-width: 300px;
            }
            QPushButton#resetBtn {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 18px;
                min-width: 300px;
            }
            QPushButton#resetBtn:hover {
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
        main_layout.addWidget(self._create_reset_form())
        main_layout.addWidget(self._create_illustration())
        self.password.setEnabled(False)
        self.confirm_password.setEnabled(False)
        self.setLayout(main_layout)

    def _create_reset_form(self):
        """Create and return the registration form widget."""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(50, 50, 50, 50)
        left_layout.setSpacing(15)

        title = QLabel("Reset Password")
        title.setFont(QFont("Arial", 48, QFont.Bold))
        title.setStyleSheet("color: #333; font-size: 48px;")

        self.email = QLineEdit()
        self.email.setText(self.current_email)
        self.email.setReadOnly(True)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter New Password...")
        self.password.setEchoMode(QLineEdit.Password)
        LoginDialog.add_toggle_action(self.password, self)

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm New Password...")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        LoginDialog.add_toggle_action(self.confirm_password, self)

        reset_btn = QPushButton("Reset Password")
        reset_btn.setObjectName("resetBtn")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self.reset_password)

        left_layout.addWidget(title)
        left_layout.addSpacing(20)
        left_layout.addWidget(QLabel("Email"))
        left_layout.addWidget(self.email)
        left_layout.addWidget(QLabel("New Password"))
        left_layout.addWidget(self.password)
        left_layout.addWidget(QLabel("Confirm New Password"))
        left_layout.addWidget(self.confirm_password)
        left_layout.addSpacing(10)
        left_layout.addWidget(reset_btn)
        left_layout.addStretch()
        left_layout.addWidget(self._create_logo())

        left_widget.setLayout(left_layout)
        return left_widget

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

    def show_reset_fields(self):
        """Show the reset password fields after OTP verified."""
        self.password.setEnabled(True)
        self.confirm_password.setEnabled(True)
        self.otp_verified = True

    def _hash_password(self, password):
        """Hash the password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def reset_password(self):
        """Handle the registration process with validation."""
        email = self.email.text().strip()
        password = self.password.text()
        confirm_password = self.confirm_password.text()

        if not password or not confirm_password:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
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

        users_file = get_database_path("users.json")
        password_hash = self._hash_password(password)
        
        try:
            # load existing user data
            with open(users_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            # update password for the user
            for user in data["users"]:
                if user["email"].lower() == email.lower():
                    user["password_hash"] = password_hash
                    break

            # save updated data
            with open(users_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
            
            QMessageBox.information(
                self, "Success", "Password has been reset succesfully"
            )
            self.accept()
        
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "User database not found")
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Invalid database format")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error resetting password: {str(e)}")

    def _verify_email_otp(self):
        """Handle the email OTP verification process."""
        otp_dialog = OTPDialog(self.otp_verification, self.current_email, self)
        if otp_dialog.exec_() == QDialog.Accepted:
            self.show_reset_fields()
