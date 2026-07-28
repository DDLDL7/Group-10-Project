"""GridCare-Lite entry point (PySide6 desktop app)."""
import sys

from PySide6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
