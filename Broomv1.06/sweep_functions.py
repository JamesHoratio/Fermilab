# sweep_functions.py

import pyvisa
import time
import numpy as np
from config import *

class PulsedIVTest:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.instrument = None
        self.start = 0
        self.stop = 0
        self.step = 0
        self.delay = 0
        self.U = []
        self.I = []

    def connect(self):
        try:
            self.instrument = self.rm.open_resource(INSTRUMENT_ADDRESS)
            self.instrument.timeout = TIMEOUT
            self.instrument.write_termination = '\n'
            self.instrument.read_termination = '\n'
            print(CONNECTION_SUCCESS)
            return True
        except pyvisa.errors.VisaIOError as e:
            print(f"{CONNECTION_ERROR} {str(e)}")
            return False

    def disconnect(self):
        if self.instrument:
            self.instrument.close()
            self.instrument = None
        self.rm.close()
        print(DISCONNECTION_MESSAGE)

    def get_status(self):
        return self.instrument.query("*IDN?")

    def reset(self):
        self.instrument.write('*RST')
        time.sleep(SETUP_DELAY)

    def set_linear_staircase(self):
        self.instrument.write('SOUR:SWE:SPAC LIN')
        time.sleep(SETUP_DELAY)

    def set_logarithmic_staircase(self):
        self.instrument.write('SOUR:SWE:SPAC LOG')
        time.sleep(SETUP_DELAY)

    def set_start_current(self, start_current):
        self.instrument.write(f'SOUR:CURR:STAR {start_current}')
        self.start = float(start_current)
        time.sleep(SETUP_DELAY)

    def set_stop_current(self, stop_current):
        self.instrument.write(f'SOUR:CURR:STOP {stop_current}')
        self.stop = float(stop_current)
        time.sleep(SETUP_DELAY)

    def set_step(self, step):
        self.instrument.write(f'SOUR:CURR:STEP {step}')
        self.step = float(step)
        time.sleep(SETUP_DELAY)

    def set_delay(self, delay):
        self.instrument.write(f'SOUR:DEL {delay}')
        self.delay = float(delay)
        time.sleep(SETUP_DELAY)

    def set_span(self):
        self.instrument.write('SOUR:PDEL:RANG BEST')
        time.sleep(SETUP_DELAY)

    def set_current_compliance(self, compliance):
        self.instrument.write(f'SOUR:CURR:COMP {compliance}')
        time.sleep(SETUP_DELAY)

    def set_pulse_width(self, width):
        self.instrument.write(f'SOUR:PDEL:WIDT {width}')
        time.sleep(SETUP_DELAY)

    def set_pulse_delay(self, delay):
        self.instrument.write(f'SOUR:PDEL:SDEL {delay}')
        time.sleep(SETUP_DELAY)

    def set_pulse_interval(self, interval):
        self.instrument.write(f'SOUR:PDEL:INT {interval}')
        time.sleep(SETUP_DELAY)

    def set_sweep_mode(self, state='ON'):
        self.instrument.write(f'SOUR:PDEL:SWE {state}')
        time.sleep(SETUP_DELAY)

    def set_pulse_count(self, count):
        self.instrument.write(f'SOUR:PDEL:COUN {count}')
        time.sleep(SETUP_DELAY)

    def set_buffer_size(self, size=DEFAULT_BUFFER_SIZE):
        self.instrument.write(f'TRAC:POIN {size}')
        time.sleep(SETUP_DELAY)

    def clean_buffer(self):
        self.instrument.write('TRAC:CLE')
        time.sleep(SETUP_DELAY)

    def set_pulse_low_level(self, level):
        self.instrument.write(f'SOUR:PDEL:LOW {level}')
        time.sleep(SETUP_DELAY)

    def set_low_measure_enable(self, count):
        self.instrument.write(f'SOUR:PDEL:LME {count}')
        time.sleep(SETUP_DELAY)

    def arm(self):
        self.instrument.write('SOUR:PDEL:ARM')
        time.sleep(SETUP_DELAY)

    def initialize(self):
        self.instrument.write('INIT:IMM')
        time.sleep(SETUP_DELAY)

    def abort(self):
        self.instrument.write('ABOR')
        time.sleep(SETUP_DELAY)

    def get_data(self):
        data = self.instrument.query_ascii_values('TRAC:DATA?')
        self.U = data[::2]  # Odd indices are voltage readings
        self.I = data[1::2]  # Even indices are current readings
        return np.array(self.U), np.array(self.I)

    def calc_data_delay(self):
        return ((self.stop - self.start) / self.step) * self.delay

    def send_command_to_2182A(self, command):
        self.instrument.write(f':SYST:COMM:SER:SEND "{command}"')
        time.sleep(0.1)  # Wait for command to be processed
        response = self.instrument.query(':SYST:COMM:SER:ENT?')
        return response

    def query_2182A(self, query):
        self.send_command_to_2182A(query)
        response = self.instrument.query(':SYST:COMM:SER:ENT?')
        return response

    def set_2182A_voltage_range(self, voltage_range):
        voltage_range_values = {'100 mV': 0.1, '1 V': 1, '10 V': 10, '100 V': 100}
        numerical_voltage_range = voltage_range_values[voltage_range]
        self.send_command_to_2182A(f':SENS:VOLT:RANG {numerical_voltage_range}')

    def run_pulsed_sweep(self, start, stop, num_pulses, sweep_type, voltage_range, 
                         pulse_width, pulse_delay, pulse_interval, voltage_compliance,
                         pulse_off_level, num_off_measurements):
        self.reset()
        self.set_start_current(start)
        self.set_stop_current(stop)
        self.set_step((stop - start) / (num_pulses - 1) if num_pulses > 1 else 0)
        
        if sweep_type.upper() == 'LINEAR':
            self.set_linear_staircase()
        else:
            self.set_logarithmic_staircase()
        
        self.set_pulse_width(pulse_width)
        self.set_pulse_delay(pulse_delay)
        self.set_pulse_interval(pulse_interval)
        self.set_current_compliance(voltage_compliance)
        self.set_span()
        self.set_pulse_low_level(pulse_off_level)
        self.set_low_measure_enable(num_off_measurements)
        self.set_pulse_count(num_pulses)
        self.set_sweep_mode('ON')
        self.set_2182A_voltage_range(voltage_range)
        self.clean_buffer()
        self.set_buffer_size()
        
        self.arm()
        self.initialize()
        time.sleep(self.calc_data_delay() + 1)
        
        return self.get_data()

# Usage example
if __name__ == "__main__":
    test = PulsedIVTest()
    if test.connect():
        voltage, current = test.run_pulsed_sweep(0, 10e-3, 11, 'LINEAR', '100 mV', 0.0002, 0.0001, 0.1, 10, 0, 2)
        print("Voltage:", voltage)
        print("Current:", current)
        test.disconnect()
    else:
        print("Failed to connect to the instrument.")