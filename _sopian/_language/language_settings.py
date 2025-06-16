from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from .language_manager import LanguageManager


class LanguageSettingsWidget(QWidget):
    def __init__(self, language_manager: LanguageManager, parent=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.init_ui()

        # Connect language change signal
        self.language_manager.text_changed.connect(self.update_text)

    def init_ui(self):
        layout = QVBoxLayout()

        # Language selection
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel(self.language_manager.get_text("language") + ":")
        self.lang_combo = QComboBox()

        # Add available languages
        for lang_code in self.language_manager.get_available_languages():
            lang_name = self._get_language_name(lang_code)
            self.lang_combo.addItem(lang_name, lang_code)

        # Set current language
        current_index = self.lang_combo.findData(self.language_manager.current_language)
        if current_index >= 0:
            self.lang_combo.setCurrentIndex(current_index)

        lang_layout.addWidget(self.lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # Save button
        self.save_btn = QPushButton(self.language_manager.get_text("save"))
        self.save_btn.clicked.connect(self.save_language)
        layout.addWidget(self.save_btn)

        layout.addStretch()
        self.setLayout(layout)

    def _get_language_name(self, lang_code):
        """Get the display name for a language code"""
        language_names = {
            "en": "English",
            "id": "Bahasa Indonesia",
            "es": "Español",
            "de": "Deutsch",
        }
        return language_names.get(lang_code, lang_code)

    def save_language(self):
        """Save the selected language"""
        lang_code = self.lang_combo.currentData()
        if self.language_manager.set_language(lang_code):
            QMessageBox.information(
                self,
                self.language_manager.get_text("success"),
                self.language_manager.get_text("settings_saved"),
            )
        else:
            QMessageBox.warning(
                self,
                self.language_manager.get_text("error"),
                "Failed to change language",
            )

    def update_text(self, key, new_text):
        """Update text when language changes"""
        if key == "language":
            self.lang_label.setText(new_text + ":")
        elif key == "save":
            self.save_btn.setText(new_text)
        elif key == "success":
            self.success_text = new_text
        elif key == "settings_saved":
            self.settings_saved_text = new_text
        elif key == "error":
            self.error_text = new_text
