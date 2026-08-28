"""Reports screen: open outage count, average resolution time, outages by region."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout, QHeaderView, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from models.reports import summary


class ReportsScreen(QWidget):
    def __init__(self, database):
        super().__init__()
        self.database = database

        title = QLabel("GridCare-Lite Reports")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        self.stats_row = QHBoxLayout()
        self.total_label = QLabel()
        self.open_label = QLabel()
        self.resolved_label = QLabel()
        self.avg_label = QLabel()
        for label in (self.total_label, self.open_label, self.resolved_label, self.avg_label):
            label.setStyleSheet("font-size: 13px;")
            self.stats_row.addWidget(label)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load)

        region_title = QLabel("Outages by Region")
        region_title.setStyleSheet("font-size: 15px; font-weight: 600; margin-top: 10px;")

        self.region_table = QTableWidget(0, 2)
        self.region_table.setHorizontalHeaderLabels(["Region", "Outages"])
        self.region_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.region_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addLayout(self.stats_row)
        layout.addWidget(refresh_button)
        layout.addWidget(region_title)
        layout.addWidget(self.region_table)
        self.setLayout(layout)

        self.load()

    def load(self):
        stats = summary(self.database)
        self.total_label.setText(f"Total Outages: {stats['total_outages']}")
        self.open_label.setText(f"Open Outages: {stats['open_outages']}")
        self.resolved_label.setText(f"Resolved: {stats['resolved_outages']}")
        self.avg_label.setText(f"Avg. Resolution: {stats['average_resolution_hours']:.2f} h")

        self.region_table.setRowCount(len(stats["by_region"]))
        for i, (region, count) in enumerate(stats["by_region"]):
            self.region_table.setItem(i, 0, QTableWidgetItem(region))
            self.region_table.setItem(i, 1, QTableWidgetItem(str(count)))
