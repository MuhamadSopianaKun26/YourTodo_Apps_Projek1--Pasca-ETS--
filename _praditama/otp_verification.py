import random
import smtplib
from email.message import EmailMessage
from PyQt5.QtWidgets import QMessageBox
from datetime import datetime, timedelta

class OTPVerification:
    def __init__(self):
        self.otp = ""
        self.otp_expired_time = None
        self.from_email = "admnyourtodo@gmail.com"
        self.app_password = "liwjclcpcnfxvgfp"

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
                "This OTP is valid for 5 minutes.\n"
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
        return datetime.now() - self.otp_expired_time > timedelta(minutes=5)

    def verify_otp(self, user_input):

        if self.is_otp_expired():
            QMessageBox.warning(None, "OTP Expired", "The OTP has expired. Please request a new one.")
            return False
        
        if user_input == self.otp:
            return True
        else:
            QMessageBox.warning(None, "Verification Failed", "The OTP you entered is incorrect.")
            return False