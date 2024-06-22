"""
Helps easily create GUIs for PyVISA instrumentation.

Provides class InstrumentOption which encapsulates information about a particular GUI option,
and function open_gui_return_input which takes in a list of InstrumentOptions, creates a GUI,
and returns the user's input when the GUI submit button is pressed.

GUI is formatted as a singular column of instrument options, with each option input presented 
as either a text box or check box.

Typical usage example:
    instrument_options = [
            InstrumentOption("High Current", "high_current", "0.001"),
            InstrumentOption("Filter Type", "filter_type"),
            InstrumentOption("Use Low to Earth", "lowToEarth_on", False, True),
            InstrumentOption("Use Input Capacitor", "inputCap_on", False, True),
        ]

    messages = "Message to display in GUI"

    parameters = open_gui_return_input(
        instrument_options, messages, "saved_parameters.txt"
    )


    Copyright 2023 Tektronix, Inc.                      
    See www.tek.com/sample-license for licensing terms. 

"""
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import colorchooser
from tkinter import font
from tkinter import scrolledtext
from tkinter import Menu
from tkinter import Spinbox
from tkinter import messagebox
from tkinter import Canvas
from tkinter import PanedWindow
from tkinter import Listbox
from tkinter import Checkbutton
from tkinter import Radiobutton
from tkinter import Scale
from tkinter import LabelFrame
from tkinter import Menu
from tkinter import Menubutton
from tkinter import OptionMenu
from instrcomms import Communications

class InstrumentOption:
    """Class that encapsulates information about instrument parameters to present on GUI.

    A list of these can be passed to function open_gui_return_input() in order to automatically
    generate a Tkinter GUI window for getting instrument parameters from a user.

    Attributes:
        option_label: A string indicating the option name displayed in the GUI.
        gui_key: The key (string) used to retrieve the input value from Tkinter.
        default_value: A string (or bool if is_bool is True) indicating the default GUI value.
        is_bool: A boolean indicating if the GUI option should be a text field or boolean checkbox.
    """

    def __init__(
        self,
        label: str,
        gui_key: str,
        default_value="0",
        is_bool: bool = False,
        tooltip: str = "",
        permanent_tooltip=False,
    ) -> None:
        self.label = label
        self.gui_key = gui_key
        self.default_value = default_value
        self.is_bool = is_bool
        self.tooltip = tooltip
        self.permanent_tooltip = permanent_tooltip

    def tkinter_row(self, parent, label_length: int = 30):
        """Creates a Tkinter row for the instrument option input"""
        row = ttk.Frame(parent)
        
        # Create option label
        option_label = ttk.Label(row, text=self.label, width=label_length)
        option_label.pack(side=tk.LEFT)
        
        if self.is_bool:
            var = tk.BooleanVar(value=self.default_value)
            input_widget = ttk.Checkbutton(row, variable=var)
        else:
            var = tk.StringVar(value=self.default_value)
            input_widget = ttk.Entry(row, textvariable=var, width=10)
        
        input_widget.pack(side=tk.LEFT)
        
        # Create tooltip if permanent_tooltip is True
        if self.permanent_tooltip and self.tooltip:
            tooltip_label = ttk.Label(row, text=self.tooltip, font=("Arial", 10, "italic"))
            tooltip_label.pack(side=tk.LEFT)
        
        return row, var


def open_gui_return_input(instrument_options, messages: str, saved_parameters_filename: str):
    """Create GUI window with options specified by instrument_options, return input on user submit.

    Args:
        instrument_options (object): List of InstrumentOption objects to be added to GUI.

        messages (str): String that will be displayed as a note on the GUI window.

        saved_parameters_filename (str): Path name of file where user parameters will be saved
            to and reloaded from.

    Returns:
        (dict): Dictionary containing instrument parameters entered in the GUI, with keys determined
            by the gui_key attributes of the InstrumentOption objects in instrument_options.
    """
    # Open the parameters file or create one
    try:
        with open(saved_parameters_filename, "r", encoding="utf-8") as file:
            saved_params = file.read().splitlines()
    except FileNotFoundError:
        with open(saved_parameters_filename, "x", encoding="utf-8") as file:
            saved_params = []

    # Set GUI parameter default values to previously saved parameters
    if len(saved_params) == len(instrument_options):
        for i, value in enumerate(saved_params):
            if instrument_options[i].is_bool:
                instrument_options[i].default_value = True if value == "True" else False
            else:
                instrument_options[i].default_value = value

    # Create main Tkinter window
    root = tk.Tk()
    root.title("Instrument Parameter GUI")

    # Get max length of any instrument_option label, used for alignment
    max_label_length = max(len(option.label) for option in instrument_options)

    # Create main frame
    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Create and add instrument option rows
    var_dict = {}
    for i, option in enumerate(instrument_options):
        row, var = option.tkinter_row(main_frame, label_length=max_label_length)
        row.grid(row=i, column=0, sticky=tk.W, pady=2)
        var_dict[option.gui_key] = var

    # Create message label
    message_label = ttk.Label(main_frame, text=messages, wraplength=300, justify=tk.CENTER)
    message_label.grid(row=len(instrument_options), column=0, pady=10)

    # Create submit button
    def on_submit():
        with open(saved_parameters_filename, "w", encoding="utf-8") as file:
            for key, var in var_dict.items():
                file.write(str(var.get()) + "\n")
        root.quit()

    submit_button = ttk.Button(main_frame, text="Run Test", command=on_submit)
    submit_button.grid(row=len(instrument_options) + 1, column=0, pady=10)

    def on_close():
        # Close the instrument here
        inst_6221 = Communications("GPIB0::12::INSTR")
        inst_6221.connect()
        inst_6221.write(":sour:swe:abort")
        inst_6221.write(":SYST:COMM:SERIAL:SEND \"*RST\"")
        inst_6221.write("*RST")
        #inst_6221.disconnect()   
        #root.quit()
        print("Program Closed.")
        sys.exit(0)

    quit_button = ttk.Button(main_frame, text="Quit and Abort", command=on_close)
    quit_button.grid(row=len(instrument_options) + 2, column=0, pady=10)
    root.mainloop()

    return {key: var.get() for key, var in var_dict.items()}
