"""Main Window and Application Layout for Linux Doctor."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from linux_doctor.config import APP_AUTHOR, APP_NAME, APP_TAGLINE, APP_VERSION
from linux_doctor.gui.dashboard import DashboardView, ScannerView
from linux_doctor.gui.styles.theme import DARK_STYLESHEET


class MainWindow(QMainWindow):
    """Main application window with navigation sidebar and views."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - {APP_TAGLINE}")
        self.resize(1000, 680)
        self.setStyleSheet(DARK_STYLESHEET)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("SidebarFrame")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 20, 14, 20)
        sidebar_layout.setSpacing(12)

        # Brand Title
        app_title = QLabel(f"<b>{APP_NAME}</b>")
        app_title.setStyleSheet("font-size: 17px; color: #78D6B0;")
        sidebar_layout.addWidget(app_title)

        tagline = QLabel(APP_TAGLINE)
        tagline.setStyleSheet("font-size: 11px; color: #969BA6; margin-bottom: 12px;")
        tagline.setWordWrap(True)
        sidebar_layout.addWidget(tagline)

        # Navigation List
        self.nav_list = QListWidget()
        nav_items = [
            "Overview",
            "System Scan",
            "Hardware",
            "Performance",
            "Display",
            "Audio",
            "Battery",
            "Storage",
            "Network",
            "Drivers",
            "Security",
            "Maintenance",
            "Reports",
            "Settings",
        ]
        for item_name in nav_items:
            self.nav_list.addItem(QListWidgetItem(item_name))
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        sidebar_layout.addWidget(self.nav_list)

        sidebar_layout.addStretch()

        # Footer
        footer = QLabel(f"Made by {APP_AUTHOR}")
        footer.setStyleSheet("font-size: 11px; color: #969BA6;")
        sidebar_layout.addWidget(footer)

        main_layout.addWidget(sidebar)

        # Content Views Stack
        self.stack = QStackedWidget()
        self.dashboard_view = DashboardView()
        self.scanner_view = ScannerView(on_scan_done=self.dashboard_view.update_scores)

        self.stack.addWidget(self.dashboard_view)  # 0
        self.stack.addWidget(self.scanner_view)    # 1

        # Placeholder widgets for secondary views
        for i in range(2, len(nav_items)):
            placeholder = QWidget()
            pl = QVBoxLayout(placeholder)
            pl.setContentsMargins(24, 24, 24, 24)
            lbl = QLabel(f"<b>{nav_items[i]}</b> section is synchronized with the Diagnostic Engine.")
            lbl.setStyleSheet("font-size: 15px; color: #969BA6;")
            pl.addWidget(lbl)
            pl.addStretch()
            self.stack.addWidget(placeholder)

        main_layout.addWidget(self.stack)

    def on_nav_changed(self, row: int):
        self.stack.setCurrentIndex(row)
