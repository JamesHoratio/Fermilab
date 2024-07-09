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
        time.sleep(3)  # Wait for reset to complete
        self.instrument.write(':FORM:ELEM READ,SOUR')
        time.sleep(0.1)
        self.instrument.write(f':SOUR:CURR:STAR {start_level}')
        time.sleep(0.1)
        self.instrument.write(f':SOUR:CURR:STOP {stop_level}')
        time.sleep(0.1)
        self.instrument.write(f':SOUR:PDEL:COUN {num_pulses}')
        time.sleep(0.1)
        self.instrument.write(f':SOUR:SWE:SPAC {sweep_type}')
        time.sleep(0.1)
        self.instrument.write(':SOUR:PDEL:SWE ON')
        time.sleep(0.1)
        self.instrument.write(':SOUR:DEL 0.001')  # 100 µs delay between pulses
        time.sleep(0.1)
        self.instrument.write(':SOUR:PDEL:ARM')
        time.sleep(5)
        
    def run_measurement(self):
        self.instrument.write(':INIT:IMM')
        time.sleep(5)  # Wait for measurement to complete
        
    def get_data(self):
        data = self.instrument.query_ascii_values(':TRAC:DATA?')
        voltage = data[::2]  # Odd indices are voltage readings
        current = data[1::2]  # Even indices are current readings
        return np.array(voltage), np.array(current)
    
    def close(self):
        self.instrument.close()
        self.rm.close()

# Usage example
if __name__ == '__main__':
    test = PulsedIVTest()
    test.setup_sweep(0, 10e-3, 11, 'LIN')
    test.run_measurement()
    test.instrument.write(':SOUR:SWE:ABOR')
    time.sleep(4)
    voltage, current = test.get_data()
    print(voltage)
    print(current)
    test.close()