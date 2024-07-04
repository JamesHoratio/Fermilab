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
        
        self.gui.set_start_measurement_callback(self.run_measurement)
        self.gui.set_abort_callback(self.abort_measurement)
        self.gui.set_connect_callback(self.connect_instrument)
        self.gui.set_disconnect_callback(self.disconnect_instrument)
        
    def run(self):
        self.gui.mainloop()
        
    def connect_instrument(self):
        if self.pulsed_iv.connect():
            messagebox.showinfo("Connection", CONNECTION_SUCCESS)
            self.gui.enable_controls()
        else:
            messagebox.showerror("Connection Error", CONNECTION_ERROR)

    def disconnect_instrument(self):
        self.pulsed_iv.disconnect()
        self.gui.disable_controls()
        messagebox.showinfo("Disconnection", DISCONNECTION_MESSAGE)
        
    def run_measurement(self, start, stop, num_pulses, sweep_type, voltage_range, 
                        pulse_width, pulse_delay, pulse_interval, voltage_compliance,
                        pulse_off_level, num_off_measurements):
        try:
            self.gui.disable_controls()
            self.gui.abort_button.config(state=tk.NORMAL)
            
            self.pulsed_iv.setup_pulsed_sweep(
                start, stop, num_pulses, sweep_type, voltage_range,
                pulse_width, pulse_delay, pulse_interval, voltage_compliance,
                pulse_off_level, num_off_measurements
            )
            self.pulsed_iv.run_measurement()
            voltage, current = self.pulsed_iv.get_data()
            
            self.gui.update_graph(current, voltage)
            messagebox.showinfo("Measurement Complete", MEASUREMENT_COMPLETE)
            
            # Save data to file
            self.save_data_to_file(voltage, current)
            
        except Exception as e:
            messagebox.showerror("Measurement Error", MEASUREMENT_ERROR.format(str(e)))
        finally:
            self.gui.enable_controls()
            self.gui.abort_button.config(state=tk.DISABLED)

    def abort_measurement(self):
        try:
            self.pulsed_iv.abort_measurement()
            messagebox.showinfo("Measurement Aborted", "The measurement was aborted.")
        except Exception as e:
            messagebox.showerror("Abort Error", f"Error while aborting measurement: {str(e)}")

    def save_data_to_file(self, voltage, current):
        filename = f"{DEFAULT_FILE_PREFIX}{time.strftime('%Y%m%d_%H%M%S')}{DEFAULT_FILE_EXTENSION}"
        try:
            with open(filename, 'w') as f:
                f.write("Voltage (V),Current (A)\n")
                for v, i in zip(voltage, current):
                    f.write(f"{v},{i}\n")
            messagebox.showinfo("File Saved", f"Data saved to {filename}")
        except Exception as e:
            messagebox.showerror("File Save Error", f"Error saving data: {str(e)}")

if __name__ == "__main__":
    controller = BroomController()
    controller.run()