"""Technician view: that technician's own work orders, with status actions."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from models.work_orders import list_work_orders_for_technician, update_status

COLUMNS = ["Work Order ID", "Outage ID", "Substation", "Scheduled Date", "Status"]


class TechnicianOrdersScreen(QWidget):
    def __init__(self, database, user):
        super().__init__()
        self.database = database
        self.user = user

        title = QLabel("My Work Orders")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        in_progress_button = QPushButton("Mark In Progress")
        in_progress_button.clicked.connect(lambda: self._update("In Progress"))
        complete_button = QPushButton("Mark Completed")
        complete_button.clicked.connect(lambda: self._update("Completed"))
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_orders)

        button_row = QHBoxLayout()
        button_row.addWidget(in_progress_button)
        button_row.addWidget(complete_button)
        button_row.addWidget(refresh_button)
        button_row.addStretch()

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.table)
        layout.addLayout(button_row)
        self.setLayout(layout)

        self.load_orders()

    def load_orders(self):
        rows = list_work_orders_for_technician(self.database, self.user.user_id)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            values = [row["work_order_id"], row["outage_id"], row["substation"],
                      row["scheduled_date"], row["status"]]
            for j, value in enumerate(values):
                self.table.setItem(i, j, QTableWidgetItem(str(value if value is not None else "")))

    def _update(self, new_status: str):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.critical(self, "Error", "Select a work order first.")
            return
        work_order_id = int(self.table.item(selected[0].row(), 0).text())
        try:
            update_status(self.database, self.user, work_order_id, new_status)
        except (ValueError, PermissionError) as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return
        QMessageBox.information(self, "Success", f"Work order marked '{new_status}'.")
        self.load_orders()
