"""Grid Analysis screen: browse the substation/line reference data imported
from the grid-analysis component, and view its pre-generated charts.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox, QHeaderView, QLabel, QScrollArea, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from models.grid_analysis import list_charts, list_lines, list_substations

SUBSTATION_COLUMNS = ["ID", "Name", "Region"]
LINE_COLUMNS = ["ID", "Source", "Destination", "Length (km)", "Voltage (kV)"]


def _table(columns: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    return table


class GridAnalysisScreen(QWidget):
    def __init__(self, database):
        super().__init__()
        self.database = database

        title = QLabel("Grid Analysis")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.tabs = QTabWidget()
        self.tabs.addTab(self._substations_tab(), "Substations")
        self.tabs.addTab(self._lines_tab(), "Lines")
        self.tabs.addTab(self._charts_tab(), "Charts")

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.resize(700, 550)

    # -- Substations -----------------------------------------------------

    def _substations_tab(self) -> QWidget:
        tab = QWidget()
        self.substation_table = _table(SUBSTATION_COLUMNS)
        rows = list_substations(self.database)
        self.substation_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            values = [row["substation_id"], row["name"], row["region"]]
            for j, value in enumerate(values):
                self.substation_table.setItem(i, j, QTableWidgetItem(str(value)))
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"{len(rows)} substations"))
        layout.addWidget(self.substation_table)
        tab.setLayout(layout)
        return tab

    # -- Lines -------------------------------------------------------------

    def _lines_tab(self) -> QWidget:
        tab = QWidget()
        self.line_table = _table(LINE_COLUMNS)
        rows = list_lines(self.database)
        self.line_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            values = [
                row["line_id"], row["source_substation"], row["destination_substation"],
                row["length_km"], row["voltage_kv"],
            ]
            for j, value in enumerate(values):
                self.line_table.setItem(i, j, QTableWidgetItem(str(value if value is not None else "")))
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"{len(rows)} lines"))
        layout.addWidget(self.line_table)
        tab.setLayout(layout)
        return tab

    # -- Charts --------------------------------------------------------

    def _charts_tab(self) -> QWidget:
        tab = QWidget()
        self.charts = list_charts()

        self.chart_selector = QComboBox()
        self.chart_selector.addItems([path.stem.replace("_", " ").title() for path in self.charts])
        self.chart_selector.currentIndexChanged.connect(self._show_chart)

        self.chart_image = QLabel("No charts found")
        self.chart_image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        scroll = QScrollArea()
        scroll.setWidget(self.chart_image)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout()
        layout.addWidget(self.chart_selector)
        layout.addWidget(scroll)
        tab.setLayout(layout)

        if self.charts:
            self._show_chart(0)
        return tab

    def _show_chart(self, index: int):
        if not (0 <= index < len(self.charts)):
            return
        pixmap = QPixmap(str(self.charts[index]))
        if pixmap.isNull():
            self.chart_image.setText(f"Could not load {self.charts[index].name}")
            return
        scaled = pixmap.scaledToWidth(640, Qt.TransformationMode.SmoothTransformation)
        self.chart_image.setPixmap(scaled)
