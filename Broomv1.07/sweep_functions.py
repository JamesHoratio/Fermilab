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

    def reset_6221(self):
        self.instrument.write('*RST')
        time.sleep(SETUP_DELAY)

    def query_6221(self):
        return self.instrument.query('*IDN?')

    def reset_2182a(self):
        self.send_command_to_2182A('*RST')

    def query_2182a(self):
        return self.query_2182A('*IDN?')

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

    def set_2182a_voltage_range(self, voltage_range):
        voltage_range_values = {'100 mV': 0.1, '1 V': 1, '10 V': 10, '100 V': 100}
        numerical_voltage_range = voltage_range_values[voltage_range]
        self.send_command_to_2182A(f':SENS:VOLT:RANG {numerical_voltage_range}')

    def configure_2182a(self):
        commands = [
            '*RST',
            ':SENS:FUNC "VOLT"',
            ':SENS:CHAN 1',
            ':SENS:VOLT:NPLC 1',
            ':TRIG:SOUR EXT',
            ':TRIG:DEL 0',
            ':TRIG:COUN 1',
            ':SYST:AZER:STAT OFF',
            ':SYST:LSYN:STAT OFF'
        ]
        for command in commands:
            self.send_command_to_2182A(command)
    
    def configure_trigger_link(self):
        # Configure 6221
        self.instrument.write(':TRIG:SOUR TLINK')
        self.instrument.write(':TRIG:DIR SOURCE')
        self.instrument.write(':TRIG:OUTP SOUR')
        self.instrument.write(':TRIG:INPU SENS')
        self.instrument.write(':TRIG:OLIN 1')
        self.instrument.write(':TRIG:ILIN 1')

        # Configure 2182A
        self.send_command_to_2182A(':TRIG:SOUR TLINK')
        self.send_command_to_2182A(':TRIG:ILIN 1')

    def set_compliance_abort(self, state):
        self.instrument.write(f':SOUR:CURR:PROT:MODE {"LATE" if state else "RSCD"}')

    def arm(self):
        self.instrument.write(':SOUR:PDEL:ARM')

    def check_arm_status(self):
        return self.instrument.query(':SOUR:PDEL:ARM?')

    def initiate(self):
        self.instrument.write(':INIT:IMM')

    def abort(self):
        self.instrument.write(':SOUR:SWE:ABORT')

    def get_data(self):
        data = self.instrument.query_ascii_values(':TRAC:DATA?')
        self.U = data[::2]  # Odd indices are voltage readings
        self.I = data[1::2]  # Even indices are current readings
        return np.array(self.U), np.array(self.I)

    def send_command_to_2182A(self, command):
        self.instrument.write(f':SYST:COMM:SER:SEND "{command}"')
        time.sleep(0.2)  # Wait for command to be processed

    def query_2182A(self, query):
        self.send_command_to_2182A(query)
        return self.instrument.query(':SYST:COMM:SER:ENT?')

    def log_message(self, message):
        # This method can be connected to the GUI's log_to_terminal method
        print(message)  # Default behavior is to print to console

    def setup_pulsed_sweep(self, start, stop, num_pulses, sweep_type, voltage_range, 
                           pulse_width, pulse_delay, pulse_interval, voltage_compliance,
                           pulse_off_level, num_off_measurements):
        self.reset_6221()
        self.reset_2182a()
        self.configure_2182a()
        self.configure_trigger_link()

        self.set_2182a_voltage_range(voltage_range)
        self.set_start_current(start)
        self.set_stop_current(stop)
        self.set_step((stop-start)/(num_pulses-1))
        self.set_linear_staircase() if sweep_type.upper() == 'LINEAR' else self.set_logarithmic_staircase()
        self.set_pulse_width(pulse_width)
        self.set_pulse_delay(pulse_delay)
        self.set_pulse_interval(pulse_interval)
        self.set_current_compliance(voltage_compliance)
        self.set_span()
        self.set_pulse_low_level(pulse_off_level)
        self.set_low_measure_enable(num_off_measurements)
        self.set_pulse_count(num_pulses)
        self.set_sweep_mode('ON')
        self.clean_buffer()
        self.set_buffer_size()

    def run_pulsed_sweep(self, start, stop, num_pulses, sweep_type, voltage_range, 
                         pulse_width, pulse_delay, pulse_interval, voltage_compliance,
                         pulse_off_level, num_off_measurements, enable_compliance_abort):
        try:
            self.setup_pulsed_sweep(start, stop, num_pulses, sweep_type, voltage_range,
                                    pulse_width, pulse_delay, pulse_interval, voltage_compliance,
                                    pulse_off_level, num_off_measurements)
            self.set_compliance_abort(enable_compliance_abort)
            
            self.log_message("Setup complete. Arming instruments...")
            self.arm()
            
            arm_status = self.check_arm_status()
            self.log_message(f"Arm status: {arm_status}")
            
            user_response = input("Do you want to continue with the sweep? (yes/no): ")
            if user_response.lower() != 'yes':
                self.log_message("Sweep aborted by user.")
                return None, None
            
            self.log_message("Initiating sweep...")
            self.initiate()
            
            self.log_message("Sweep in progress...")
            time.sleep(num_pulses * float(pulse_interval) + 1)  # Estimate sweep time
            
            self.log_message("Retrieving data...")
            voltage, current = self.get_data()
            
            self.log_message("Sweep completed successfully.")
            return voltage, current
        
        except Exception as e:
            self.log_message(f"An error occurred during the sweep: {str(e)}")
            self.abort()
            return None, None

# Usage example
if __name__ == "__main__":
    test = PulsedIVTest()
    if test.connect():
        v, i = test.run_pulsed_sweep(0, 10e-3, 11, 'LINEAR', '100 mV', 0.0002, 0.0001, 5, 10, 0, 2, True)
        if v is not None and i is not None:
            print("Voltage:", v)
            print("Current:", i)
        test.disconnect()
    else:
        print("Failed to connect to the instrument.")
