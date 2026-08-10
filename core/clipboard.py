from PySide6.QtWidgets import QApplication


class ClipboardService:
    @staticmethod
    def copy_text(text: str) -> bool:
        if not text:
            return False

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        return clipboard.text() == text