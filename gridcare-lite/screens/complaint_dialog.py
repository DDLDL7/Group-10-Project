"""Customer complaint log: form, optionally linked to an outage ID."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox, QTextEdit, QVBoxLayout,
)

from models.complaints import log_complaint


class ComplaintDialog(QDialog):
    def __init__(self, database, user, parent=None):
        super().__init__(parent)
        self.database = database
        self.user = user
        self.setWindowTitle("Log Customer Complaint")
        self.resize(420, 320)

        self.customer_name_input = QLineEdit()
        self.outage_id_input = QLineEdit()
        self.outage_id_input.setPlaceholderText("optional")
        self.description_input = QTextEdit()

        form = QFormLayout()
        form.addRow("Customer Name:", self.customer_name_input)
        form.addRow("Known Outage ID:", self.outage_id_input)
        form.addRow("Complaint:", self.description_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Save Complaint")
        buttons.accepted.connect(self.submit)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def submit(self):
        name = self.customer_name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        outage_text = self.outage_id_input.text().strip()

        outage_id = None
        if outage_text:
            try:
                outage_id = int(outage_text)
            except ValueError:
                QMessageBox.critical(self, "Error", "Outage ID must be a number.")
                return

        try:
            log_complaint(self.database, self.user, name, description, outage_id)
        except (ValueError, PermissionError) as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return

        QMessageBox.information(self, "Success", "Customer complaint recorded.")
        self.accept()
