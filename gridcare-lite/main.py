
"""GridCare-Lite entry point (PySide6 desktop app)."""

import sys
from PySide6.QtWidgets import QApplication
from data_model import LoginWindow


def main():
    app = QApplication(sys.argv)

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()