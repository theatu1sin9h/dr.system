"""Modern Canvas Components: Hardware Node Graph, Sparklines, and Metric Badges."""

from collections import deque
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class TelemetrySparkline(QWidget):
    """Smooth, real-time animated sparkline with subtle gradient underfills."""

    def __init__(self, color_hex: str = "#78D6B0", max_points: int = 40, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.data = deque([0.0] * max_points, maxlen=max_points)
        self.setMinimumHeight(45)
        self.setMinimumWidth(100)

    def add_data_point(self, val: float):
        self.data.append(max(0.0, min(100.0, val)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        n = len(self.data)
        if n < 2:
            return

        step = w / (n - 1)
        path = QPainterPath()
        points = []

        for i, val in enumerate(self.data):
            x = i * step
            # val is 0-100, invert for Y coord
            y = h - (val / 100.0) * (h - 8) - 4
            points.append(QPointF(x, y))

        path.moveTo(points[0])
        for p in points[1:]:
            path.lineTo(p)

        # Draw fill gradient under path
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()

        base_color = QColor(self.color_hex)
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 60))
        grad.setColorAt(1.0, QColor(base_color.red(), base_color.green(), base_color.blue(), 0))

        painter.fillPath(fill_path, QBrush(grad))

        # Draw line
        pen = QPen(base_color, 2)
        painter.setPen(pen)
        painter.drawPath(path)


class HardwareTopologyCanvas(QWidget):
    """Interactive visual topology map showing CPU, RAM, GPU, Bus, and Storage interconnects."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(240)
        self.cpu_label = "CPU: Octa-Core"
        self.ram_label = "RAM: 16 GB"
        self.gpu_label = "GPU: Integrated/Discrete"
        self.storage_label = "Storage: NVMe Block"
        self.psi_label = "PSI Stalls: 0.0%"

    def update_hardware(self, cpu: str, ram: str, gpu: str, storage: str, psi: str):
        self.cpu_label = cpu
        self.ram_label = ram
        self.gpu_label = gpu
        self.storage_label = storage
        self.psi_label = psi
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Canvas background
        painter.fillRect(self.rect(), QColor("#181A20"))

        # Node coordinates
        cx = w / 2
        cy = h / 2

        cpu_rect = QRectF(cx - 90, 20, 180, 50)
        ram_rect = QRectF(30, cy - 25, 160, 50)
        gpu_rect = QRectF(w - 190, cy - 25, 160, 50)
        storage_rect = QRectF(cx - 90, h - 70, 180, 50)

        # Bus interconnect lines
        bus_pen = QPen(QColor("#2E333D"), 2, Qt.DashLine)
        painter.setPen(bus_pen)
        painter.drawLine(cpu_rect.center(), ram_rect.center())
        painter.drawLine(cpu_rect.center(), gpu_rect.center())
        painter.drawLine(cpu_rect.center(), storage_rect.center())

        # Central Chipset Hub marker
        hub_rect = QRectF(cx - 24, cy - 24, 48, 48)
        painter.setPen(QPen(QColor("#78D6B0"), 2))
        painter.setBrush(QColor("#22252D"))
        painter.drawEllipse(hub_rect)
        painter.setPen(QColor("#78D6B0"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(hub_rect, Qt.AlignCenter, "BUS")

        # Draw Nodes
        def draw_node(rect: QRectF, title: str, subtitle: str, color_hex: str):
            painter.setPen(QPen(QColor(color_hex), 1))
            painter.setBrush(QColor("#22252D"))
            painter.drawRoundedRect(rect, 8, 8)

            painter.setPen(QColor("#F4F5F7"))
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.drawText(QRectF(rect.x() + 10, rect.y() + 8, rect.width() - 20, 18), Qt.AlignLeft, title)

            painter.setPen(QColor("#969BA6"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(QRectF(rect.x() + 10, rect.y() + 26, rect.width() - 20, 18), Qt.AlignLeft, subtitle)

        draw_node(cpu_rect, "Processor", self.cpu_label, "#78D6B0")
        draw_node(ram_rect, "Memory", self.ram_label, "#78D6B0")
        draw_node(gpu_rect, "Graphics", self.gpu_label, "#78D6B0")
        draw_node(storage_rect, "Storage Bus", self.storage_label, "#78D6B0")
