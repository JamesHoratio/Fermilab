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
        self.abort_callback = None
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Connection controls
        self.connect_button = ttk.Button(control_frame, text="Connect", command=self.on_connect)
        self.connect_button.pack(pady=5)

        self.disconnect_button = ttk.Button(control_frame, text="Disconnect", command=self.on_disconnect, state=tk.DISABLED)
        self.disconnect_button.pack(pady=5)

        # Pulsed IV Measurements controls
        ttk.Label(control_frame, text="Pulsed IV Measurements").pack(pady=10)

        ttk.Label(control_frame, text="Pulse Mode: Sweep Pulse Amplitude").pack()

        ttk.Label(control_frame, text="Start Pulse Level (A):").pack()
        self.start_level = ttk.Entry(control_frame)
        self.start_level.insert(0, "0")
        self.start_level.pack()

        ttk.Label(control_frame, text="Stop Pulse Level (A):").pack()
        self.stop_level = ttk.Entry(control_frame)
        self.stop_level.insert(0, "10E-3")
        self.stop_level.pack()

        ttk.Label(control_frame, text="Number of Pulses:").pack()
        self.num_pulses = ttk.Entry(control_frame)
        self.num_pulses.insert(0, "11")
        self.num_pulses.pack()

        ttk.Label(control_frame, text="Sweep Type:").pack()
        self.sweep_type = ttk.Combobox(control_frame, values=['Linear', 'Logarithmic'])
        self.sweep_type.set('Linear')
        self.sweep_type.pack()

        ttk.Label(control_frame, text="Voltage Measure Range:").pack()
        self.voltage_range = ttk.Combobox(control_frame, values=['100 mV', '1 V', '10 V', '100 V'])
        self.voltage_range.set('100 mV')
        self.voltage_range.pack()

        ttk.Label(control_frame, text="Pulse Width (s):").pack()
        self.pulse_width = ttk.Entry(control_frame)
        self.pulse_width.insert(0, "0.0002")
        self.pulse_width.pack()

        ttk.Label(control_frame, text="Pulse Delay (s):").pack()
        self.pulse_delay = ttk.Entry(control_frame)
        self.pulse_delay.insert(0, "0.0001")
        self.pulse_delay.pack()

        ttk.Label(control_frame, text="Interval between Pulses (s):").pack()
        self.pulse_interval = ttk.Entry(control_frame)
        self.pulse_interval.insert(0, "0.1")
        self.pulse_interval.pack()

        ttk.Label(control_frame, text="Current Source Voltage Compliance (V):").pack()
        self.voltage_compliance = ttk.Entry(control_frame)
        self.voltage_compliance.insert(0, "10")
        self.voltage_compliance.pack()

        ttk.Label(control_frame, text="Pulse Off Level (A):").pack()
        self.pulse_off_level = ttk.Entry(control_frame)
        self.pulse_off_level.insert(0, "0")
        self.pulse_off_level.pack()

        ttk.Label(control_frame, text="Number of Pulse Off Measurements:").pack()
        self.num_off_measurements = ttk.Entry(control_frame)
        self.num_off_measurements.insert(0, "2")
        self.num_off_measurements.pack()

        self.run_button = ttk.Button(control_frame, text="Run", command=self.on_run, state=tk.DISABLED)
        self.run_button.pack(pady=20)

        self.abort_button = ttk.Button(control_frame, text="Abort", command=self.on_abort, state=tk.DISABLED)
        self.abort_button.pack(pady=20)

        # Graph frame
        graph_frame = ttk.Frame(main_frame)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # X and Y axis selection
        x_axis_frame = ttk.Frame(graph_frame)
        x_axis_frame.pack()
        ttk.Label(x_axis_frame, text="X Axis:").pack(side=tk.LEFT)
        self.x_axis = ttk.Combobox(x_axis_frame, values=['Current', 'Voltage'])
        self.x_axis.set('Current')
        self.x_axis.pack(side=tk.LEFT)

        y_axis_frame = ttk.Frame(graph_frame)
        y_axis_frame.pack()
        ttk.Label(y_axis_frame, text="Y Axis:").pack(side=tk.LEFT)
        self.y_axis = ttk.Combobox(y_axis_frame, values=['Current', 'Voltage'])
        self.y_axis.set('Voltage')
        self.y_axis.pack(side=tk.LEFT)

    def on_connect(self):
        if self.connect_callback:
            self.connect_callback()

    def on_disconnect(self):
        if self.disconnect_callback:
            self.disconnect_callback()

    def on_run(self):
        if self.start_measurement:
            self.start_measurement(
                float(self.start_level.get()),
                float(self.stop_level.get()),
                int(self.num_pulses.get()),
                self.sweep_type.get(),
                self.voltage_range.get(),
                float(self.pulse_width.get()),
                float(self.pulse_delay.get()),
                float(self.pulse_interval.get()),
                float(self.voltage_compliance.get()),
                float(self.pulse_off_level.get()),
                int(self.num_off_measurements.get())
            )

    def on_abort(self):
        if self.abort_callback:
            self.abort_callback()

    def update_graph(self, x_data, y_data):
        self.ax.clear()
        self.ax.plot(x_data, y_data, 'b-')
        self.ax.set_xlabel(self.x_axis.get())
        self.ax.set_ylabel(self.y_axis.get())
        self.ax.set_title("Pulsed IV Graph")
        self.canvas.draw()

    def set_start_measurement_callback(self, callback):
        self.start_measurement = callback

    def set_abort_callback(self, callback):
        self.abort_callback = callback

    def set_connect_callback(self, callback):
        self.connect_callback = callback

    def set_disconnect_callback(self, callback):
        self.disconnect_callback = callback

    def enable_controls(self):
        self.disconnect_button.config(state=tk.NORMAL)
        self.run_button.config(state=tk.NORMAL)
        self.connect_button.config(state=tk.DISABLED)

    def disable_controls(self):
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.run_button.config(state=tk.DISABLED)
        self.abort_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = BroomGUI()
    app.mainloop()