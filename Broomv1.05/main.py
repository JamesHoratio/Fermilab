# main.py

from gui import BroomGUI
from sweep_functions import PulsedIVTest
import tkinter as tk
from tkinter import messagebox
import datetime
import time
from config import *

class BroomController:
    def __init__(self):
        self.gui = BroomGUI()
        self.pulsed_iv = PulsedIVTest()
        
        self.gui.set_start_measurement_callback(self.run_measurement)
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
        self.pulsed_iv.close()
        self.gui.disable_controls()
        messagebox.showinfo("Disconnection", DISCONNECTION_MESSAGE)
        
    def run_measurement(self, start, stop, num_pulses, sweep_type, v_range, pulse_width, pulse_delay):
        try:
            self.pulsed_iv.reset()
            self.pulsed_iv.set_linear_staircase()
            self.pulsed_iv.set_start_current(start)
            self.pulsed_iv.set_stop_current(stop)
            self.pulsed_iv.set_step((stop - start) / (num_pulses - 1))
            self.pulsed_iv.set_span()
            self.pulsed_iv.set_current_compliance(v_range)
            
            self.pulsed_iv.set_pulse_width(pulse_width)
            self.pulsed_iv.set_pulse_delay(pulse_delay)
            self.pulsed_iv.set_sweep_mode('ON')
            self.pulsed_iv.set_pulse_count(num_pulses)
            
            self.pulsed_iv.set_buffer_size()
            self.pulsed_iv.clean_buffer()
            self.pulsed_iv.initialize()
            self.pulsed_iv.run()
            self.pulsed_iv.data_processing()
            
            self.gui.update_graph(self.pulsed_iv.U, self.pulsed_iv.I)
            messagebox.showinfo("Measurement Complete", MEASUREMENT_COMPLETE)
            
            # Save data to file
            self.save_data_to_file()
            
        except Exception as e:
            messagebox.showerror("Measurement Error", MEASUREMENT_ERROR.format(str(e)))

    def save_data_to_file(self):
        filename = f"{DEFAULT_FILE_PREFIX}{time.strftime('%Y%m%d_%H%M%S')}{DEFAULT_FILE_EXTENSION}"
        try:
            with open(filename, 'w') as f:
                f.write("Voltage (V),Current (A)\n")
                for v, i in zip(self.pulsed_iv.U, self.pulsed_iv.I):
                    f.write(f"{v},{i}\n")
            messagebox.showinfo("File Saved", f"Data saved to {filename}")
        except Exception as e:
            messagebox.showerror("File Save Error", f"Error saving data: {str(e)}")

if __name__ == "__main__":
    controller = BroomController()
    controller.run()