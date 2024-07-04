# sweep_functions2.py

import pyvisa
import time
import numpy as np
from config import INSTRUMENT_ADDRESS, TIMEOUT

class PulsedIVTest:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(INSTRUMENT_ADDRESS)
        self.instrument.timeout = TIMEOUT
        self.instrument.write_termination = '\n'
        self.instrument.read_termination = '\n'
        
    def setup_sweep(self, start_level, stop_level, num_pulses, sweep_type='LIN'):
        self.instrument.write('*RST')
        self.instrument.write(':SOUR:PDEL:ARM')
        self.instrument.write(f':SOUR:PDEL:HIGH {stop_level}')
        self.instrument.write(f':SOUR:PDEL:LOW {start_level}')
        self.instrument.write(f':SOUR:PDEL:COUN {num_pulses}')
        self.instrument.write(f':SOUR:SWE:SPAC {sweep_type}')
        self.instrument.write(':SOUR:PDEL:SWE ON')
        
    def run_measurement(self):
        self.instrument.write(':INIT:IMM')
        time.sleep(1)  # Wait for measurement to complete
        
    def get_data(self):
        data = self.instrument.query_ascii_values(':TRAC:DATA?')
        voltage = data[::2]  # Odd indices are voltage readings
        current = data[1::2]  # Even indices are current readings
        return np.array(voltage), np.array(current)
    
    def close(self):
        self.instrument.close()
        self.rm.close()