"""Outage dashboard: table of outages, filterable by region and status."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from models.outages import list_outages

COLUMNS = ["Outage ID", "Substation", "Region", "Severity", "Description", "Status", "Reported At"]


class OutageDashboard(QWidget):
    def __init__(self, database):
        super().__init__()
        self.database = database

        title = QLabel("Outage Dashboard")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.region_filter = QComboBox()
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All statuses", "Open", "In Progress", "Resolved"])
        self.region_filter.currentIndexChanged.connect(self.load_outages)
        self.status_filter.currentIndexChanged.connect(self.load_outages)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_outages)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Region:"))
        filter_row.addWidget(self.region_filter)
        filter_row.addWidget(QLabel("Status:"))
        filter_row.addWidget(self.status_filter)
        filter_row.addWidget(refresh_button)
        filter_row.addStretch()

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addLayout(filter_row)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self._populate_regions()
        self.load_outages()

    def _populate_regions(self):
        self.region_filter.blockSignals(True)
        self.region_filter.clear()
        self.region_filter.addItem("All regions")
        conn = self.database.connect()
        try:
            regions = [r["region"] for r in conn.execute("SELECT DISTINCT region FROM substations ORDER BY region")]
        finally:
            conn.close()
        self.region_filter.addItems(regions)
        self.region_filter.blockSignals(False)

    def load_outages(self):
        region = self.region_filter.currentText()
        status = self.status_filter.currentText()
        region = None if region in ("", "All regions") else region
        status = None if status in ("", "All statuses") else status

        rows = list_outages(self.database, region=region, status=status)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            values = [
                row["outage_id"], row["substation"], row["region"], row["severity"],
                row["description"], row["status"], row["reported_at"],
            ]
            for j, value in enumerate(values):
                self.table.setItem(i, j, QTableWidgetItem(str(value if value is not None else "")))
