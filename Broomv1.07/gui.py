# gui.py

import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import *

class BroomGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(GUI_TITLE)
        self.geometry(GUI_WINDOW_SIZE)
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.create_connection_controls(left_frame)
        self.create_tabbed_controls(left_frame)
        self.create_graph(right_frame)
        self.create_terminal(right_frame)

    def create_connection_controls(self, parent):
        self.connect_button = ttk.Button(parent, text="Connect", command=self.on_connect)
        self.connect_button.pack(pady=5)

        self.disconnect_button = ttk.Button(parent, text="Disconnect", command=self.on_disconnect, state=tk.DISABLED)
        self.disconnect_button.pack(pady=5)

    def create_tabbed_controls(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        setup_frame = ttk.Frame(notebook)
        timing_frame = ttk.Frame(notebook)
        advanced_frame = ttk.Frame(notebook)

        notebook.add(setup_frame, text="Setup")
        notebook.add(timing_frame, text="Timing")
        notebook.add(advanced_frame, text="Advanced")

        self.create_setup_controls(setup_frame)
        self.create_timing_controls(timing_frame)
        self.create_advanced_controls(advanced_frame)

    def create_setup_controls(self, parent):
        ttk.Label(parent, text="Pulse Mode: Sweep Pulse Amplitude").pack()

        ttk.Label(parent, text="Start Pulse Level (A):").pack()
        self.start_level = ttk.Entry(parent)
        self.start_level.insert(0, "0")
        self.start_level.pack()

        ttk.Label(parent, text="Stop Pulse Level (A):").pack()
        self.stop_level = ttk.Entry(parent)
        self.stop_level.insert(0, "10E-3")
        self.stop_level.pack()

        ttk.Label(parent, text="Number of Pulses:").pack()
        self.num_pulses = ttk.Entry(parent)
        self.num_pulses.insert(0, "11")
        self.num_pulses.pack()

        ttk.Label(parent, text="Sweep Type:").pack()
        self.sweep_type = ttk.Combobox(parent, values=['Linear', 'Logarithmic'])
        self.sweep_type.set('Linear')
        self.sweep_type.pack()

        ttk.Label(parent, text="Voltage Measure Range:").pack()
        self.voltage_range = ttk.Combobox(parent, values=['100 mV', '1 V', '10 V', '100 V'])
        self.voltage_range.set('100 mV')
        self.voltage_range.pack()

    def create_timing_controls(self, parent):
        ttk.Label(parent, text="Pulse Width (s):").pack()
        self.pulse_width = ttk.Entry(parent)
        self.pulse_width.insert(0, "0.0002")
        self.pulse_width.pack()

        ttk.Label(parent, text="Pulse Delay (s):").pack()
        self.pulse_delay = ttk.Entry(parent)
        self.pulse_delay.insert(0, "0.0001")
        self.pulse_delay.pack()

        ttk.Label(parent, text="Interval between Pulses (NPLC):").pack()
        self.pulse_interval = ttk.Entry(parent)
        self.pulse_interval.insert(0, "5")
        self.pulse_interval.pack()

    def create_advanced_controls(self, parent):
        ttk.Label(parent, text="Current Source Voltage Compliance (V):").pack()
        self.voltage_compliance = ttk.Entry(parent)
        self.voltage_compliance.insert(0, "100")
        self.voltage_compliance.pack()

        ttk.Label(parent, text="Pulse Off Level (A):").pack()
        self.pulse_off_level = ttk.Entry(parent)
        self.pulse_off_level.insert(0, "0")
        self.pulse_off_level.pack()

        ttk.Label(parent, text="Number of Pulse Off Measurements:").pack()
        self.num_off_measurements = ttk.Entry(parent)
        self.num_off_measurements.insert(0, "2")
        self.num_off_measurements.pack()

        self.compliance_abort = tk.BooleanVar()
        ttk.Checkbutton(parent, text="Enable Compliance Abort", variable=self.compliance_abort).pack()

        ttk.Button(parent, text="Reset 6221", command=self.on_reset_6221).pack(pady=5)
        ttk.Button(parent, text="Query 6221", command=self.on_query_6221).pack(pady=5)
        ttk.Button(parent, text="Reset 2182A", command=self.on_reset_2182a).pack(pady=5)
        ttk.Button(parent, text="Query 2182A", command=self.on_query_2182a).pack(pady=5)

    def create_graph(self, parent):
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_terminal(self, parent):
        self.terminal = scrolledtext.ScrolledText(parent, height=10)
        self.terminal.pack(fill=tk.BOTH, expand=True)

    def on_connect(self):
        if self.connect_callback:
            self.connect_callback()

    def on_disconnect(self):
        if self.disconnect_callback:
            self.disconnect_callback()

    def on_reset_6221(self):
        if self.reset_6221_callback:
            self.reset_6221_callback()

    def on_query_6221(self):
        if self.query_6221_callback:
            self.query_6221_callback()

    def on_reset_2182a(self):
        if self.reset_2182a_callback:
            self.reset_2182a_callback()

    def on_query_2182a(self):
        if self.query_2182a_callback:
            self.query_2182a_callback()

    def update_graph(self, x_data, y_data):
        self.ax.clear()
        self.ax.plot(x_data, y_data, 'b-')
        self.ax.set_xlabel("Current (A)")
        self.ax.set_ylabel("Voltage (V)")
        self.ax.set_title("Pulsed IV Graph")
        self.canvas.draw()

    def log_to_terminal(self, message):
        self.terminal.insert(tk.END, message + "\n")
        self.terminal.see(tk.END)

    def set_connect_callback(self, callback):
        self.connect_callback = callback

    def set_disconnect_callback(self, callback):
        self.disconnect_callback = callback

    def set_reset_6221_callback(self, callback):
        self.reset_6221_callback = callback

    def set_query_6221_callback(self, callback):
        self.query_6221_callback = callback

    def set_reset_2182a_callback(self, callback):
        self.reset_2182a_callback = callback

    def set_query_2182a_callback(self, callback):
        self.query_2182a_callback = callback

    def enable_controls(self):
        self.disconnect_button.config(state=tk.NORMAL)
        self.connect_button.config(state=tk.DISABLED)

    def disable_controls(self):
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    app = BroomGUI()
    app.mainloop()