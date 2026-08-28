"""Top-level window: hosts the login screen, then a role-based dashboard
that opens the individual screens/dialogs. Role separation is enforced
here at the UI-visibility level *and* independently inside models/ (see
CurrentUser.require_role), so a role can't reach a disallowed action even
by driving the app programmatically.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QLabel, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from screens.complaint_dialog import ComplaintDialog
from screens.grid_analysis_screen import GridAnalysisScreen
from screens.login_screen import LoginScreen
from screens.new_outage_dialog import NewOutageDialog
from screens.outage_dashboard import OutageDashboard
from screens.reports_screen import ReportsScreen
from screens.technician_orders import TechnicianOrdersScreen
from screens.work_order_dialog import WorkOrderDialog


class RoleDashboard(QWidget):
    """Post-login home screen. Its button set is entirely determined by role."""

    def __init__(self, database, user, on_logout):
        super().__init__()
        self.database = database
        self.user = user
        self.on_logout = on_logout
        self._open_windows: list[QWidget] = []

        title = QLabel("GridCare-Lite")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        subtitle = QLabel(f"Welcome {user.username} | Role: {user.role}")
        subtitle.setStyleSheet("color: #555; margin-bottom: 12px;")

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(subtitle)

        if user.role == "engineer":
            layout.addWidget(self._button("Report New Outage", self.new_outage))
            layout.addWidget(self._button("View Outages", self.outage_dashboard))
        elif user.role == "admin":
            layout.addWidget(self._button("View Outages", self.outage_dashboard))
            layout.addWidget(self._button("Assign Work Order", self.assign_work_order))
            layout.addWidget(self._button("Reports", self.reports))
        elif user.role == "technician":
            layout.addWidget(self._button("My Work Orders", self.technician_orders))
        elif user.role == "customer_service":
            layout.addWidget(self._button("View Outages", self.outage_dashboard))
            layout.addWidget(self._button("Log Customer Complaint", self.complaint))

        layout.addWidget(self._button("Grid Analysis", self.grid_analysis))

        layout.addStretch()
        logout_button = QPushButton("Log Out")
        logout_button.clicked.connect(self._logout)
        layout.addWidget(logout_button)

        self.setLayout(layout)

    @staticmethod
    def _button(text: str, handler) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(handler)
        return button

    def _logout(self):
        for window in self._open_windows:
            window.close()
        self.on_logout()

    def _track(self, window: QWidget):
        self._open_windows.append(window)
        window.show()

    def outage_dashboard(self):
        self._track(OutageDashboard(self.database))

    def technician_orders(self):
        self._track(TechnicianOrdersScreen(self.database, self.user))

    def reports(self):
        self._track(ReportsScreen(self.database))

    def new_outage(self):
        NewOutageDialog(self.database, self.user, self).exec()

    def assign_work_order(self):
        WorkOrderDialog(self.database, self.user, self).exec()

    def complaint(self):
        ComplaintDialog(self.database, self.user, self).exec()

    def grid_analysis(self):
        self._track(GridAnalysisScreen(self.database))


class MainWindow(QMainWindow):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.setWindowTitle("GridCare-Lite")
        self.resize(500, 400)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_screen = LoginScreen(database)
        self.login_screen.login_succeeded.connect(self.show_dashboard)
        self.stack.addWidget(self.login_screen)

        self.dashboard: RoleDashboard | None = None

    def show_dashboard(self, user):
        if self.dashboard is not None:
            self.stack.removeWidget(self.dashboard)
            self.dashboard.deleteLater()

        self.dashboard = RoleDashboard(self.database, user, self.show_login)
        self.stack.addWidget(self.dashboard)
        self.stack.setCurrentWidget(self.dashboard)
        self.resize(700, 500)

    def show_login(self):
        self.stack.setCurrentWidget(self.login_screen)
        self.resize(500, 400)
