"""Work order assignment (admin only): assign technician, set scheduled date."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDialogButtonBox, QFormLayout, QMessageBox, QVBoxLayout,
)
from PySide6.QtCore import QDate

from models.work_orders import assign_work_order, list_open_outages, list_technicians


class WorkOrderDialog(QDialog):
    def __init__(self, database, user, parent=None):
        super().__init__(parent)
        self.database = database
        self.user = user
        self.setWindowTitle("Assign Work Order")
        self.resize(420, 260)

        self.outage_box = QComboBox()
        for outage_id, name, severity in list_open_outages(database):
            self.outage_box.addItem(f"#{outage_id} — {name} ({severity})", outage_id)

        self.technician_box = QComboBox()
        for tech_id, username in list_technicians(database):
            self.technician_box.addItem(username, tech_id)

        self.date_input = QDateEdit()
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate().addDays(1))
        self.date_input.setCalendarPopup(True)

        form = QFormLayout()
        form.addRow("Outage:", self.outage_box)
        form.addRow("Assign Technician:", self.technician_box)
        form.addRow("Scheduled Date:", self.date_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Assign Work Order")
        buttons.accepted.connect(self.submit)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

        if self.outage_box.count() == 0:
            QMessageBox.information(self, "Nothing to assign", "There are no open outages right now.")
        if self.technician_box.count() == 0:
            QMessageBox.warning(self, "No technicians", "No technician accounts exist yet.")

    def submit(self):
        if self.outage_box.currentIndex() < 0 or self.technician_box.currentIndex() < 0:
            QMessageBox.critical(self, "Error", "Select both an outage and a technician.")
            return

        outage_id = self.outage_box.currentData()
        technician_id = self.technician_box.currentData()
        scheduled_date = self.date_input.date().toString("yyyy-MM-dd")

        try:
            assign_work_order(self.database, self.user, outage_id, technician_id, scheduled_date)
        except (ValueError, PermissionError) as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return

        QMessageBox.information(self, "Success", "Work order assigned successfully.")
        self.accept()
