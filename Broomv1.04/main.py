# main.py

import sys
from PyQt5.QtWidgets import QApplication
from gui import BroomGUI
from sweep_functions2 import PulsedIVTest

class BroomController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.gui = BroomGUI()
        self.pulsed_iv = PulsedIVTest()
        
        self.gui.start_measurement.connect(self.run_measurement)
        
    def run(self):
        self.gui.show()
        sys.exit(self.app.exec_())
        
    def run_measurement(self, start, stop, num, sweep_type, v_range):
        self.pulsed_iv.setup_sweep(start, stop, num, sweep_type)
        self.pulsed_iv.run_measurement()
        voltage, current = self.pulsed_iv.get_data()
        self.gui.update_graph(voltage, current)

if __name__ == "__main__":
    controller = BroomController()
    controller.run()