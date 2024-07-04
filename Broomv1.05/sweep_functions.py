# sweep_functions.py

import pyvisa
import time
import numpy as np
from config import *

class PulsedIVTest:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.instrument = None
        self.start = DEFAULT_START_LEVEL
        self.stop = DEFAULT_STOP_LEVEL
        self.step = (DEFAULT_STOP_LEVEL - DEFAULT_START_LEVEL) / (DEFAULT_NUM_PULSES - 1)
        self.delay = float(DEFAULT_PULSE_DELAY)
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

    def get_status(self):
        return self.instrument.query("*IDN?")

    def reset(self):
        self.instrument.write('*RST')
        time.sleep(SETUP_DELAY)

    def set_linear_staircase(self):
        self.instrument.write('SOUR:SWE:SPAC LIN')
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

    def initialize(self):
        self.instrument.write('SOUR:PDEL:ARM')
        time.sleep(SETUP_DELAY)

    def run(self):
        print('The process has started...')
        self.instrument.write('INIT:IMM')
        time.sleep(self.calc_data_delay() + 1)
        print(MEASUREMENT_COMPLETE)

    def calc_data_delay(self):
        return ((self.stop - self.start) / self.step) * self.delay

    def data_processing(self):
        time.sleep(DATA_PROCESSING_DELAY)
        data = self.instrument.query('TRAC:DATA?')
        data_list = data.split(",")[::2]
        self.U = [float(number) for number in data_list]
        self.I = [self.start + i * self.step for i in range(len(self.U))]
        time.sleep(DATA_PROCESSING_DELAY)

    def close(self):
        if self.instrument:
            self.instrument.close()
        self.rm.close()
        print(DISCONNECTION_MESSAGE)

# Usage example
if __name__ == "__main__":
    test = PulsedIVTest()
    if test.connect():
        print(test.get_status())
        test.reset()
        test.set_linear_staircase()
        test.set_start_current(DEFAULT_START_LEVEL)
        test.set_stop_current(DEFAULT_STOP_LEVEL)
        test.set_step((DEFAULT_STOP_LEVEL - DEFAULT_START_LEVEL) / (DEFAULT_NUM_PULSES - 1))
        test.set_span()
        test.set_current_compliance(DEFAULT_CURRENT_COMPLIANCE)
        test.set_pulse_width(DEFAULT_PULSE_WIDTH)
        test.set_pulse_delay(DEFAULT_PULSE_DELAY)
        test.set_sweep_mode()
        test.set_pulse_count(DEFAULT_NUM_PULSES)
        test.set_buffer_size()
        test.clean_buffer()
        test.initialize()
        test.run()
        test.data_processing()
        print("Voltage:", test.U)
        print("Current:", test.I)
        test.close()
    else:
        print("Failed to connect to the instrument.")