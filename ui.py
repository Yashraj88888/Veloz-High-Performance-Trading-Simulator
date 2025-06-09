from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from websocket_client import fetch_available_assets
from websocket_client import WebSocketClient

class TradeSimulatorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget { background-color: #2c2c2c; color: white; font-size: 14pt; }
            QLabel { font-weight: bold; font-size: 16pt; }
            QLineEdit { background-color: white; color: black; border: 1px solid #ccc; 
                        border-radius: 10px; padding: 3px; }
            QPushButton { background-color: #007BFF; color: white; font-weight: bold; 
                          border-radius: 5px; padding: 5px 10px; }
            QPushButton:hover { background-color: #0056b3; }
            QComboBox { background-color: white; color: black; border: 1px solid #ccc; 
                        border-radius: 10px; padding: 3px; }
            QComboBox QAbstractItemView { background-color: lightgrey; color: #000000; 
                                          selection-background-color: #007BFF; 
                                          selection-color: white; }
        """)
        self.setWindowTitle("Real-Time Trade Simulator 2")
        self.showMaximized()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self._init_input_panel()
        self._init_output_panel()
        self.populate_assets()
        self.ws_thread = None

    def _init_input_panel(self):
        input_layout = QVBoxLayout()
        font = QFont("Arial", 28, QFont.Bold)
        exchange_label = QLabel("Veloz : Digital Asset Trading Simulator")
        exchange_label.setFont(font)
        exchange_label.setAlignment(Qt.AlignCenter)
        input_layout.addWidget(exchange_label)
        self.asset_input = QComboBox()
        self.order_type = QLineEdit("Market")
        self.qty_input = QLineEdit("100")
        self.vol_input = QLineEdit("0.5")
        self.fee_input = QComboBox()
        self.fee_input.addItems(["Tier 1", "Tier 2", "Tier 3"])
        start_btn = QPushButton("Start Simulation")
        start_btn.clicked.connect(self.start_simulation)
        self.stop_btn = QPushButton("Stop Simulation")
        self.stop_btn.setStyleSheet("background-color: red;")
        self.stop_btn.clicked.connect(self.stop_simulation)

        for label_text, widget in [
            ("Spot Asset:", self.asset_input),
            ("Order Type:", self.order_type),
            ("Order Quantity (USD):", self.qty_input),
            ("Volatility:", self.vol_input),
            ("Fee Tier:", self.fee_input),
        ]:
            label = QLabel(label_text)
            input_layout.addWidget(label)
            input_layout.addWidget(widget)
        input_layout.addSpacing(20)
        input_layout.addWidget(start_btn)
        input_layout.addSpacing(10)
        input_layout.addWidget(self.stop_btn)
        self.layout.addLayout(input_layout)

    def _init_output_panel(self):
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setStyleSheet("""
            QTextEdit { background-color: black; color: white; font-weight: bold;
                       font-size: 14pt; border-radius: 20px; padding: 8px; }
        """)
        self.layout.addWidget(self.output_box)

    def start_simulation(self):
        self.output_box.clear()
        self.stop_simulation()
        
        # Disconnect previous connections
        if self.ws_thread:
            try:
                self.ws_thread.tick_signal.disconnect()
            except:
                pass
        
        asset = self.asset_input.currentText().strip()
        qty = self.qty_input.text().strip()
        vol = self.vol_input.text().strip()
        fee_tier = self.fee_input.currentText()
        
        self.ws_thread = WebSocketClient(asset, qty, fee_tier, vol)
        self.ws_thread.tick_signal.connect(self.output_box.append)
        self.ws_thread.start()

    def stop_simulation(self):
        if self.ws_thread:
            self.ws_thread.stop()
            self.ws_thread.wait()
            self.output_box.append("Simulation stopped.\n")

    def populate_assets(self):
        assets = fetch_available_assets()
        self.asset_input.clear()
        if assets:
            self.asset_input.addItems(assets)
        else:
            self.asset_input.addItem("Failed to load assets")
