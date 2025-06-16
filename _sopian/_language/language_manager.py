from PyQt5.QtCore import QObject, pyqtSignal
import json
import os


class LanguageManager(QObject):
    language_changed = pyqtSignal(str)  # Signal emitted when language changes
    text_changed = pyqtSignal(
        str, str
    )  # Signal emitted when text changes (key, new_text)

    def __init__(self):
        super().__init__()
        self.current_language = "en"  # Default language
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        """Load all translation files from the translations directory"""
        translations_dir = os.path.join(os.path.dirname(__file__), "translations")
        if not os.path.exists(translations_dir):
            os.makedirs(translations_dir)

        for filename in os.listdir(translations_dir):
            if filename.endswith(".json"):
                lang_code = filename[:-5]  # Remove .json extension
                with open(
                    os.path.join(translations_dir, filename), "r", encoding="utf-8"
                ) as f:
                    self.translations[lang_code] = json.load(f)

    def set_language(self, lang_code):
        """Set the current language and emit signals for all text changes"""
        if lang_code in self.translations:
            old_language = self.current_language
            self.current_language = lang_code

            # Emit signals for all text changes
            for key in self.translations[lang_code]:
                new_text = self.translations[lang_code][key]
                self.text_changed.emit(key, new_text)

            # Emit language changed signal
            self.language_changed.emit(lang_code)
            return True
        return False

    def get_text(self, key, default=None):
        """Get translated text for the given key"""
        if self.current_language in self.translations:
            return self.translations[self.current_language].get(key, default or key)
        return default or key

    def get_available_languages(self):
        """Get list of available languages"""
        return list(self.translations.keys())
