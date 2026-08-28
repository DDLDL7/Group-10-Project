"""GridCare-Lite entry point (PySide6 desktop app)."""
import sys

from PySide6.QtWidgets import QApplication

from models.database import Database
from screens.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    database = Database()  # creates/migrates schema, seeds default users + substations/lines

    window = MainWindow(database)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
