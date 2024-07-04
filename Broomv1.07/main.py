# main.py

import time
from gui import BroomGUI
from sweep_functions import PulsedIVTest
import tkinter as tk
from tkinter import messagebox
from config import *

class BroomController:
    def __init__(self):
        self.gui = BroomGUI()
        self.pulsed_iv = PulsedIVTest()
        
        self.gui.set_connect_callback(self.connect_instrument)
        self.gui.set_disconnect_callback(self.disconnect_instrument)
        self.gui.set_reset_6221_callback(self.reset_6221)
        self.gui.set_query_6221_callback(self.query_6221)
        self.gui.set_reset_2182a_callback(self.reset_2182a)
        self.gui.set_query_2182a_callback(self.query_2182a)
        
        # Add Run and Abort buttons with their callbacks
        self.gui.run_button = tk.Button(self.gui, text="Run", command=self.run_measurement)
        self.gui.run_button.pack(pady=5)
        self.gui.abort_button = tk.Button(self.gui, text="Abort", command=self.abort_measurement)
        self.gui.abort_button.pack(pady=5)
        
        # Connect the log_message method of PulsedIVTest to the GUI's log_to_terminal method
        self.pulsed_iv.log_message = self.gui.log_to_terminal
        
    def run(self):
        self.gui.mainloop()
        
    def connect_instrument(self):
        if self.pulsed_iv.connect():
            self.gui.log_to_terminal(CONNECTION_SUCCESS)
            self.gui.enable_controls()
        else:
            self.gui.log_to_terminal(CONNECTION_ERROR)

    def disconnect_instrument(self):
        self.pulsed_iv.disconnect()
        self.gui.disable_controls()
        self.gui.log_to_terminal(DISCONNECTION_MESSAGE)

    def reset_6221(self):
        self.pulsed_iv.reset_6221()
        self.gui.log_to_terminal("6221 has been reset.")

    def query_6221(self):
        response = self.pulsed_iv.query_6221()
        self.gui.log_to_terminal(f"6221 query response: {response}")

    def reset_2182a(self):
        self.pulsed_iv.reset_2182a()
        self.gui.log_to_terminal("2182A has been reset.")

    def query_2182a(self):
        response = self.pulsed_iv.query_2182a()
        self.gui.log_to_terminal(f"2182A query response: {response}")

    def run_measurement(self):
        try:
            start = float(self.gui.start_level.get())
            stop = float(self.gui.stop_level.get())
            num_pulses = int(self.gui.num_pulses.get())
            sweep_type = self.gui.sweep_type.get()
            voltage_range = self.gui.voltage_range.get()
            pulse_width = float(self.gui.pulse_width.get())
            pulse_delay = float(self.gui.pulse_delay.get())
            pulse_interval = float(self.gui.pulse_interval.get())
            voltage_compliance = float(self.gui.voltage_compliance.get())
            pulse_off_level = float(self.gui.pulse_off_level.get())
            num_off_measurements = int(self.gui.num_off_measurements.get())
            enable_compliance_abort = self.gui.compliance_abort.get()

            voltage, current = self.pulsed_iv.run_pulsed_sweep(
                start, stop, num_pulses, sweep_type, voltage_range,
                pulse_width, pulse_delay, pulse_interval, voltage_compliance,
                pulse_off_level, num_off_measurements, enable_compliance_abort
            )

            if voltage is not None and current is not None:
                self.gui.update_graph(current, voltage)
                self.gui.log_to_terminal("Measurement completed successfully.")
            else:
                self.gui.log_to_terminal("Measurement failed or was aborted.")

        except Exception as e:
            self.gui.log_to_terminal(f"An error occurred: {str(e)}")

    def abort_measurement(self):
        self.pulsed_iv.abort()
        self.gui.log_to_terminal("Measurement aborted.")

if __name__ == "__main__":
    controller = BroomController()
    controller.run()