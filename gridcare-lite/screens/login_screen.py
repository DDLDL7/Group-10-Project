"""Login screen: routes to the correct dashboard by role on success."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from models.auth import login


class LoginScreen(QWidget):
    login_succeeded = Signal(object)  # emits a CurrentUser

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.setWindowTitle("GridCare-Lite — Login")

        title = QLabel("GridCare-Lite")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.attempt_login)

        form = QFormLayout()
        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)

        login_button = QPushButton("Log In")
        login_button.clicked.connect(self.attempt_login)

        hint = QLabel(
            "Demo accounts:\n"
            "admin / Admin123!\n"
            "engineer / Engineer123!\n"
            "technician / Technician123!\n"
            "customer_service / Service123!"
        )
        hint.setStyleSheet("color: #666; font-size: 11px;")

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(login_button)
        layout.addWidget(hint)
        layout.addStretch()
        self.setLayout(layout)

    def attempt_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        try:
            user = login(self.database, username, password)
        except ValueError as exc:
            QMessageBox.critical(self, "Login Failed", str(exc))
            return
        self.password_input.clear()
        self.login_succeeded.emit(user)
