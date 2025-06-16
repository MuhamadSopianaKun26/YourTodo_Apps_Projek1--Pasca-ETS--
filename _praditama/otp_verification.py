import random
import smtplib
from email.message import EmailMessage
from PyQt5.QtWidgets import (
    QMessageBox,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QDialog
)
from PyQt5.QtCore import QTimer, Qt
from datetime import datetime, timedelta

class OTPVerification:
    def __init__(self):
        self.otp = ""
        self.otp_expired_time = None
        self.from_email = "admnyourtodo@gmail.com"
        self.app_password = "liwjclcpcnfxvgfp"
        self.remaining_minutes = 1

    def generate_otp(self):
        self.otp = ""
        for i in range(6):
            self.otp += str(random.randint(0, 9))
            self.otp_expired_time = datetime.now()
        return self.otp 

    def send_otp(self, to_email):
        try:
            msg = EmailMessage()
            msg['Subject'] = 'OTP Verification'
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg.set_content(
                f"Your OTP is: {self.otp}\n\n"
                "This OTP is valid for 1 minutes.\n"
                "Please use this OTP to verify your email address.\n"
                "If you did not request this, please ignore this email.\n\n"
                "Regards,\n"
                "Your To-Do App Team"
            )

            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.from_email, self.app_password)
                server.send_message(msg)
            return True
        
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to send OTP: {str(e)}")
            return False
        
    def is_otp_expired(self):
        if not self.otp_expired_time:
            return True
        return datetime.now() - self.otp_expired_time > timedelta(minutes=self.remaining_minutes)
    
    def get_remaining_time(self):
        if not self.otp_expired_time or self.is_otp_expired():
            return 0
        remaining_time = (self.otp_expired_time + timedelta(minutes=self.remaining_minutes)) - datetime.now()
        return max(0, remaining_time.total_seconds())

    def verify_otp(self, user_input):
        if self.is_otp_expired():
            return False
        
        return user_input == self.otp
    
class OTPDialog(QDialog):
    def __init__(self, otp_verification, email, parent=None):
        super().__init__(parent)
        self.otp_verification = otp_verification
        self.setWindowTitle("OTP Verification")
        self.email = email
        self.setFixedSize(400, 200)
        self.verified = False
        self.init_ui()
        self.send_otp()

    def init_ui(self):
        layout = QVBoxLayout()

        self.countdown_label = QLabel("Time remaining: 1:00")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.countdown_label)

        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter OTP")
        self.otp_input.setMaxLength(6)
        layout.addWidget(self.otp_input)

        verify_button = QPushButton("Verify OTP")
        verify_button.clicked.connect(self.verify)
        layout.addWidget(verify_button)

        self.resend_button = QPushButton("Resend OTP")
        self.resend_button.setEnabled(False)
        self.resend_button.clicked.connect(self.resend_otp)
        layout.addWidget(self.resend_button)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
    
    def send_otp(self):
        self.otp_verification.generate_otp()
        if self.otp_verification.send_otp(self.email):
            self.resend_button.setEnabled(False)
            self.countdown_label.setText("Time remaining: 1:00")
            self.timer.start(1000)
        else:
            QMessageBox.critical(self, "Error", "Failed to send OTP. Please try again.")
            self.reject()
    
    def update_countdown(self):
        remaining_time = int(self.otp_verification.get_remaining_time())
        if remaining_time <= 0:
            self.countdown_label.setText("OTP expired")
            self.resend_button.setEnabled(True)
            self.timer.stop()
        else:
            minutes, seconds = divmod(remaining_time, 60)
            self.countdown_label.setText(f"Time remaining: {minutes}:{seconds:02d}")
    
    def verify(self):
        otp = self.otp_input.text()
        if not otp:
            QMessageBox.warning(self, "Error", "Please enter the OTP")
            return
        
        if self.otp_verification.verify_otp(otp):
            self.verified = True
            QMessageBox.information(self, "Success", "OTP verified successfully!")
            self.accept()
        else:
            if self.otp_verification.is_otp_expired():
                QMessageBox.warning(self, "Error", "OTP has expired")
            else:
                QMessageBox.warning(self, "Error", "Invalid OTP")

    def resend_otp(self):
        self.send_otp()