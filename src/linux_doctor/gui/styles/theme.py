"""Modern Theme and Style Palette for Linux Doctor.

Follows the specified design system:
- Background: #101114
- Surface: #181A20
- Secondary Surface: #22252D
- Primary Accent: #78D6B0
- Text: #F4F5F7
- Secondary Text: #969BA6
- Warning: #E9B96E
- Critical: #E47777
"""

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #101114;
    color: #F4F5F7;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

QFrame#SidebarFrame {
    background-color: #181A20;
    border-right: 1px solid #22252D;
}

QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    padding: 10px 14px;
    border-radius: 6px;
    color: #969BA6;
    font-weight: 500;
}

QListWidget::item:hover {
    background-color: #22252D;
    color: #F4F5F7;
}

QListWidget::item:selected {
    background-color: #22252D;
    color: #78D6B0;
    font-weight: bold;
}

QFrame.CardFrame {
    background-color: #181A20;
    border: 1px solid #22252D;
    border-radius: 10px;
    padding: 16px;
}

QPushButton {
    background-color: #22252D;
    color: #F4F5F7;
    border: 1px solid #2E333D;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #2A2E38;
    border-color: #78D6B0;
}

QPushButton#PrimaryButton {
    background-color: #78D6B0;
    color: #101114;
    border: none;
}

QPushButton#PrimaryButton:hover {
    background-color: #62C49C;
}

QProgressBar {
    background-color: #22252D;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #F4F5F7;
    height: 8px;
}

QProgressBar::chunk {
    background-color: #78D6B0;
    border-radius: 4px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}
"""
