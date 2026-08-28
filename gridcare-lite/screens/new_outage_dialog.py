"""New outage form: substation picker, description, severity."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QTextEdit, QVBoxLayout,
)

from models.outages import SEVERITIES, list_substations, report_outage


class NewOutageDialog(QDialog):
    def __init__(self, database, user, parent=None):
        super().__init__(parent)
        self.database = database
        self.user = user
        self.setWindowTitle("Report New Outage")
        self.resize(420, 320)

        self.substation_box = QComboBox()
        self._substations = list_substations(database)
        for sid, name, region in self._substations:
            self.substation_box.addItem(f"{name} ({region})", sid)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Describe the fault/outage...")

        self.severity_box = QComboBox()
        self.severity_box.addItems(list(SEVERITIES))

        form = QFormLayout()
        form.addRow("Substation:", self.substation_box)
        form.addRow("Description:", self.description_input)
        form.addRow("Severity:", self.severity_box)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Submit Outage")
        buttons.accepted.connect(self.submit)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

        if not self._substations:
            QMessageBox.warning(
                self, "No substations",
                "No substations are loaded. Import substations.csv from the grid-analysis "
                "component before logging outages.",
            )

    def submit(self):
        if self.substation_box.currentIndex() < 0:
            QMessageBox.critical(self, "Error", "Please select a substation.")
            return

        substation_id = self.substation_box.currentData()
        description = self.description_input.toPlainText().strip()
        severity = self.severity_box.currentText()

        try:
            report_outage(self.database, self.user, substation_id, description, severity)
        except ValueError as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return

        QMessageBox.information(self, "Success", "Outage successfully reported.")
        self.accept()
