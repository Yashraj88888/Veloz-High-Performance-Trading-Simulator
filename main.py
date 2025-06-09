import sys
from PyQt5.QtWidgets import QApplication
from ui import TradeSimulatorUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TradeSimulatorUI()
    win.show()
    sys.exit(app.exec_())
