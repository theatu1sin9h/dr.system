"""GUI Dashboard and Interactive Diagnostics Views (Linux Doctor 2.0).

Features Real-time animated sparklines, hardware bus topology map,
and cross-subsystem causality warnings.
"""

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
import psutil
from linux_doctor.config import APP_AUTHOR, APP_NAME, APP_TAGLINE, APP_VERSION
from linux_doctor.core.detector import OSDetector, OSInfo
from linux_doctor.core.findings import FindingSeverity, ModuleResult
from linux_doctor.core.scanner import DiagnosticScanner
from linux_doctor.gui.components.canvas import HardwareTopologyCanvas, TelemetrySparkline


class ScanWorker(QThread):
    progress_signal = Signal(str, int, int)
    finished_signal = Signal(dict, object, list)

    def __init__(self, scanner: DiagnosticScanner):
        super().__init__()
        self.scanner = scanner

    def run(self):
        def callback(name, current, total, res):
            self.progress_signal.emit(name, current, total)

        results = self.scanner.run_scan(progress_callback=callback)
        self.finished_signal.emit(results, self.scanner.score_report, self.scanner.causality_insights)


class DashboardView(QWidget):
    """Overview dashboard displaying interactive topology, sparklines, and causality insights."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.os_info: OSInfo = OSDetector.detect()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Score Card
        score_card = QFrame()
        score_card.setProperty("class", "CardFrame")
        score_layout = QHBoxLayout(score_card)

        info_layout = QVBoxLayout()
        title_label = QLabel(f"<b>AUTONOMOUS HARDWARE LAB</b> • {self.os_info.name} {self.os_info.version}")
        title_label.setStyleSheet("color: #969BA6; font-size: 13px;")
        arch_label = QLabel(f"Architecture: {self.os_info.architecture} | Kernel: {self.os_info.kernel}")
        arch_label.setStyleSheet("color: #F4F5F7; font-size: 14px;")
        info_layout.addWidget(title_label)
        info_layout.addWidget(arch_label)

        score_layout.addLayout(info_layout)
        score_layout.addStretch()

        score_box = QVBoxLayout()
        self.score_val = QLabel("100")
        self.score_val.setStyleSheet("font-size: 42px; font-weight: 800; color: #78D6B0;")
        self.score_label = QLabel("EXCELLENT")
        self.score_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #78D6B0;")
        score_box.addWidget(self.score_val, alignment=Qt.AlignCenter)
        score_box.addWidget(self.score_label, alignment=Qt.AlignCenter)
        score_layout.addLayout(score_box)

        layout.addWidget(score_card)

        # Real-time Telemetry Sparklines
        spark_card = QFrame()
        spark_card.setProperty("class", "CardFrame")
        spark_layout = QHBoxLayout(spark_card)
        spark_layout.setContentsMargins(14, 12, 14, 12)

        # CPU sparkline
        cpu_col = QVBoxLayout()
        self.cpu_lbl = QLabel("CPU Utilization: 0%")
        self.cpu_lbl.setStyleSheet("font-weight: 600; color: #F4F5F7;")
        self.cpu_spark = TelemetrySparkline(color_hex="#78D6B0")
        cpu_col.addWidget(self.cpu_lbl)
        cpu_col.addWidget(self.cpu_spark)
        spark_layout.addLayout(cpu_col)

        # RAM sparkline
        ram_col = QVBoxLayout()
        self.ram_lbl = QLabel("RAM Load: 0%")
        self.ram_lbl.setStyleSheet("font-weight: 600; color: #78D6B0;")
        self.ram_spark = TelemetrySparkline(color_hex="#E9B96E")
        ram_col.addWidget(self.ram_lbl)
        ram_col.addWidget(self.ram_spark)
        spark_layout.addLayout(ram_col)

        layout.addWidget(spark_card)

        # Hardware Bus Interconnect Canvas
        self.canvas = HardwareTopologyCanvas()
        layout.addWidget(self.canvas)

        # Causality Insight container
        self.causality_box = QFrame()
        self.causality_box.setProperty("class", "CardFrame")
        self.causality_layout = QVBoxLayout(self.causality_box)
        c_title = QLabel("<b>Cross-Subsystem Causality Engine</b>")
        c_title.setStyleSheet("font-size: 14px; color: #78D6B0;")
        self.causality_layout.addWidget(c_title)
        self.causality_text = QLabel("Autonomous correlator active. No bottleneck cross-talk detected.")
        self.causality_text.setStyleSheet("color: #969BA6; font-size: 12px;")
        self.causality_layout.addWidget(self.causality_text)
        layout.addWidget(self.causality_box)

        layout.addStretch()

        # Telemetry update timer (every 1s)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick_telemetry)
        self.timer.start(1000)

    def tick_telemetry(self):
        try:
            cpu_p = psutil.cpu_percent(interval=None)
            ram_p = psutil.virtual_memory().percent
            self.cpu_lbl.setText(f"CPU Utilization: {cpu_p:.0f}%")
            self.ram_lbl.setText(f"RAM Load: {ram_p:.0f}%")
            self.cpu_spark.add_data_point(cpu_p)
            self.ram_spark.add_data_point(ram_p)
        except Exception:
            pass

    def update_scores(self, report, causality_insights=None):
        self.score_val.setText(str(report.overall_score))
        self.score_label.setText(report.status_label)
        color = "#78D6B0"
        if report.overall_score < 60:
            color = "#E47777"
        elif report.overall_score < 75:
            color = "#E9B96E"
        self.score_val.setStyleSheet(f"font-size: 42px; font-weight: 800; color: {color};")
        self.score_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {color};")

        if causality_insights:
            first = causality_insights[0]
            self.causality_text.setText(
                f"<b>Root Cause:</b> {first.cause_component} → <b>Affected:</b> {first.affected_component}\n"
                f"{first.explanation}"
            )


class ScannerView(QWidget):
    """Interactive diagnostic scanner page with live progress."""

    def __init__(self, on_scan_done=None, parent=None):
        super().__init__(parent)
        self.scanner = DiagnosticScanner()
        self.on_scan_done = on_scan_done
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Autonomous Hardware & OS Diagnostics (2.0)")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #F4F5F7;")
        layout.addWidget(header)

        desc = QLabel("Executes synthetic thermal decay profiling, kernel PSI latency audits, and safe storage jitter sweeps.")
        desc.setStyleSheet("color: #969BA6; font-size: 13px;")
        layout.addWidget(desc)

        # Controls & Progress
        ctrl_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Full Autonomous Scan")
        self.start_btn.setObjectName("PrimaryButton")
        self.start_btn.clicked.connect(self.start_scan)
        ctrl_layout.addWidget(self.start_btn)
        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to scan.")
        self.status_label.setStyleSheet("color: #969BA6;")
        layout.addWidget(self.status_label)

        # Results area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setSpacing(10)
        self.results_layout.addStretch()
        self.scroll.setWidget(self.results_container)
        layout.addWidget(self.scroll)

    def start_scan(self):
        self.start_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Autonomous analysis in progress...")

        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.worker = ScanWorker(self.scanner)
        self.worker.progress_signal.connect(self.on_progress)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, name: str, current: int, total: int):
        pct = int((current / total) * 100)
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"Analyzing {name} ({current}/{total})...")

    def on_finished(self, results: dict, report, insights: list):
        self.start_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Scan complete! System Health: {report.overall_score}/100 ({report.status_label})")

        for key, res in results.items():
            card = QFrame()
            card.setProperty("class", "CardFrame")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 12, 12, 12)

            color = "#78D6B0" if res.status == "passed" else ("#E9B96E" if res.status == "warning" else "#E47777")
            mod_title = QLabel(f"<b>{res.display_name}</b> — <span style='color:{color};'>{res.status.upper()}</span> ({res.score:.1f}/100)")
            cl.addWidget(mod_title)

            for finding in res.findings:
                f_box = QLabel(
                    f"<b>• {finding.title}</b>\n"
                    f"  What was detected: {finding.what_detected}\n"
                    f"  Safe next step: {finding.safe_next_step}"
                )
                f_box.setStyleSheet("color: #969BA6; font-size: 12px; margin-left: 10px;")
                cl.addWidget(f_box)

            self.results_layout.insertWidget(self.results_layout.count() - 1, card)

        if self.on_scan_done:
            self.on_scan_done(report, insights)
