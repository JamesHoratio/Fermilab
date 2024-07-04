# gui.py

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import *

class BroomGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(GUI_TITLE)
        self.geometry(GUI_WINDOW_SIZE)
        self.connect_callback = None
        self.disconnect_callback = None
        self.start_measurement = None
        self.create_widgets()

    def create_widgets(self):
        control_frame = ttk.Frame(self)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.connect_button = ttk.Button(control_frame, text="Connect", command=self.on_connect)
        self.connect_button.pack(pady=5)

        self.disconnect_button = ttk.Button(control_frame, text="Disconnect", command=self.on_disconnect, state=tk.DISABLED)
        self.disconnect_button.pack(pady=5)

        ttk.Label(control_frame, text="Start Level (A):").pack()
        self.start_level = ttk.Entry(control_frame)
        self.start_level.insert(0, str(DEFAULT_START_LEVEL))
        self.start_level.pack()

        ttk.Label(control_frame, text="Stop Level (A):").pack()
        self.stop_level = ttk.Entry(control_frame)
        self.stop_level.insert(0, str(DEFAULT_STOP_LEVEL))
        self.stop_level.pack()

        ttk.Label(control_frame, text="Number of Pulses:").pack()
        self.num_pulses = ttk.Entry(control_frame)
        self.num_pulses.insert(0, str(DEFAULT_NUM_PULSES))
        self.num_pulses.pack()

        ttk.Label(control_frame, text="Sweep Type:").pack()
        self.sweep_type = ttk.Combobox(control_frame, values=['LIN', 'LOG'])
        self.sweep_type.set(DEFAULT_SWEEP_TYPE)
        self.sweep_type.pack()

        ttk.Label(control_frame, text="Voltage Range:").pack()
        self.voltage_range = ttk.Combobox(control_frame, values=VOLTAGE_RANGES)
        self.voltage_range.set(DEFAULT_VOLTAGE_RANGE)
        self.voltage_range.pack()

        ttk.Label(control_frame, text="Pulse Width (s):").pack()
        self.pulse_width = ttk.Entry(control_frame)
        self.pulse_width.insert(0, DEFAULT_PULSE_WIDTH)
        self.pulse_width.pack()

        ttk.Label(control_frame, text="Pulse Delay (s):").pack()
        self.pulse_delay = ttk.Entry(control_frame)
        self.pulse_delay.insert(0, DEFAULT_PULSE_DELAY)
        self.pulse_delay.pack()

        self.run_button = ttk.Button(control_frame, text="Run", command=self.on_run, state=tk.DISABLED)
        self.run_button.pack(pady=20)

        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def on_connect(self):
        if self.connect_callback:
            self.connect_callback()

    def on_disconnect(self):
        if self.disconnect_callback:
            self.disconnect_callback()

    def on_run(self):
        if self.start_measurement:
            start = float(self.start_level.get())
            stop = float(self.stop_level.get())
            num = int(self.num_pulses.get())
            sweep = self.sweep_type.get()
            v_range = self.voltage_range.get()
            p_width = self.pulse_width.get()
            p_delay = self.pulse_delay.get()
            self.start_measurement(start, stop, num, sweep, v_range, p_width, p_delay)

    def update_graph(self, voltage, current):
        self.ax.clear()
        self.ax.plot(current, voltage, 'b-')
        self.ax.set_xlabel(X_AXIS_LABEL)
        self.ax.set_ylabel(Y_AXIS_LABEL)
        self.ax.set_title(GRAPH_TITLE)
        self.canvas.draw()

    def set_start_measurement_callback(self, callback):
        self.start_measurement = callback

    def set_connect_callback(self, callback):
        self.connect_callback = callback

    def set_disconnect_callback(self, callback):
        self.disconnect_callback = callback

    def enable_controls(self):
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)
        self.run_button.config(state=tk.NORMAL)

    def disable_controls(self):
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.run_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = BroomGUI()
    app.mainloop()