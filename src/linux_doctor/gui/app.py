"""GUI Application Bootstrap."""

import sys
from PySide6.QtWidgets import QApplication
from linux_doctor.gui.main_window import MainWindow


def run_gui():
    """Runs the PySide6 Qt GUI."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
