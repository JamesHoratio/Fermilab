import os
import time
import datetime
import textwrap
from instrcomms import Communications
from instrgui import InstrumentOption, open_gui_return_input

DEBUG_PRINT_COMMANDS = True

start_time = time.time()  # Define the 'start_time' variable

instrument = Communications()  # Define the 'instrument' variable
query2182Apresent = int(instrument.query("sour:pdel:nvpresent?"))
if query2182Apresent == 0:
        print("2182A not present")
        instrument.disconnect()
        stop_time = time.time()  # Stop the timer...
        print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")
        exit()

instrument.write("*RST")  # Reset the instrument to its default settings
instrument.write("syst:")  # Enable the source output