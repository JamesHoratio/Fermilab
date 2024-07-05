# sweep_functions.py

import pyvisa
import time
import numpy as np
from config import *

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
            self.log_message(CONNECTION_SUCCESS)
            return True
        except pyvisa.errors.VisaIOError as e:
            self.log_message(f"{CONNECTION_ERROR} {str(e)}")
            return False

    def disconnect(self):
        if self.instrument:
            self.instrument.close()
            self.instrument = None
        self.rm.close()
        self.log_message(DISCONNECTION_MESSAGE)

    def reset_6221(self):
        self.instrument.write('*RST')
        time.sleep(SETUP_DELAY)
        self.log_message("6221 has been reset.")

    def query_6221(self):
        response = self.instrument.query('*IDN?')
        time.sleep(QUERY_DELAY)
        self.log_message(f"6221 query response: {response}")
        return response

    def reset_2182a(self):
        self.send_command_to_2182A('*RST')
        time.sleep(SETUP_DELAY)
        self.log_message("2182A has been reset.")

    def query_2182a(self):
        response = self.query_2182A('*IDN?')
        time.sleep(QUERY_DELAY)
        self.log_message(f"2182A query response: {response}")
        return response

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
        voltage_range_values = {'100 mV': 0.1, '1 V': 1, '10 V': 10, '100 V': 100, '10 mA': 'CURR:10mA'}
        numerical_voltage_range = voltage_range_values[voltage_range]
        if voltage_range == '10 mA':
            self.send_command_to_2182A(f':SENS:FUNC "CURR"')
            self.send_command_to_2182A(f':SENS:CURR:RANG {numerical_voltage_range}')
        else:
            self.send_command_to_2182A(f':SENS:FUNC "VOLT"')
            self.send_command_to_2182A(f':SENS:VOLT:RANG {numerical_voltage_range}')
        time.sleep(SETUP_DELAY)
        self.log_message(f"2182A range set to {voltage_range}")

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
            time.sleep(SETUP_DELAY)
        self.log_message("2182A configured.")

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
        time.sleep(SETUP_DELAY)
        self.log_message("Trigger link configured.")

    def set_compliance_abort(self, state):
        self.instrument.write(f':SOUR:CURR:PROT:MODE {"LATE" if state else "RSCD"}')
        time.sleep(SETUP_DELAY)
        self.log_message(f"Compliance abort set to {'LATE' if state else 'RSCD'}")

    def setup_pulsed_sweep(self, start, stop, num_pulses, sweep_type, voltage_range, 
                           pulse_width, pulse_delay, pulse_interval, voltage_compliance,
                           pulse_off_level, num_off_measurements):
        self.log_message("Setting up pulsed sweep...")
        self.reset_6221()
        self.reset_2182a()
        self.configure_2182a()
        self.configure_trigger_link()

        self.set_2182a_voltage_range(voltage_range)
        self.set_start_current(start)
        self.set_stop_current(stop)
        self.set_step((stop-start)/(num_pulses-1))
        self.set_sweep_type(sweep_type)
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

        self.log_message("Pulsed sweep setup complete.")
        self.verify_setup()

    def verify_setup(self):
        self.log_message("Verifying setup...")
        # Add verification for each parameter
        self.verify_parameter(':SOUR:CURR:START?', self.start, "Start current")
        self.verify_parameter(':SOUR:CURR:STOP?', self.stop, "Stop current")
        self.verify_parameter(':SOUR:CURR:STEP?', self.step, "Current step")
        self.verify_parameter(':SOUR:SWE:SPAC?', self.sweep_type, "Sweep type")
        self.verify_parameter(':SOUR:PDEL:WIDT?', self.pulse_width, "Pulse width")
        self.verify_parameter(':SOUR:PDEL:SDEL?', self.pulse_delay, "Pulse delay")
        self.verify_parameter(':SOUR:PDEL:INT?', self.pulse_interval, "Pulse interval")
        self.verify_parameter(':SENS:VOLT:PROT?', self.voltage_compliance, "Voltage compliance")
        self.verify_parameter(':SOUR:PDEL:LOW?', self.pulse_off_level, "Pulse off level")
        self.verify_parameter(':SOUR:PDEL:COUN?', self.pulse_count, "Pulse count")
        self.log_message("Setup verification complete.")

    def verify_parameter(self, query, expected_value, parameter_name):
        actual_value = self.instrument.query(query).strip()
        time.sleep(QUERY_DELAY)
        if float(actual_value) == float(expected_value):
            self.log_message(f"{parameter_name} verified: {actual_value}")
        else:
            self.log_message(f"Warning: {parameter_name} mismatch. Expected: {expected_value}, Actual: {actual_value}")

    def arm(self):
        self.instrument.write(':SOUR:PDEL:ARM')
        time.sleep(SETUP_DELAY)
        self.log_message("Instrument armed.")

    def check_arm_status(self):
        status = self.instrument.query(':SOUR:PDEL:ARM?')
        time.sleep(QUERY_DELAY)
        self.log_message(f"Arm status: {status}")
        return status

    def initiate(self):
        self.instrument.write(':INIT:IMM')
        time.sleep(SETUP_DELAY)
        self.log_message("Sweep initiated.")

    def abort(self):
        self.instrument.write(':ABOR')
        time.sleep(SETUP_DELAY)
        self.log_message("Sweep aborted.")

    def get_data(self):
        self.log_message("Retrieving data...")
        data = self.instrument.query_ascii_values(':TRAC:DATA?')
        time.sleep(QUERY_DELAY)
        self.U = data[::2]  # Odd indices are voltage readings
        self.I = data[1::2]  # Even indices are current readings
        self.log_message(f"Retrieved {len(self.U)} data points.")
        return np.array(self.U), np.array(self.I)

    def send_command_to_2182A(self, command):
        self.instrument.write(f':SYST:COMM:SER:SEND "{command}"')
        time.sleep(SETUP_DELAY)

    def query_2182A(self, query):
        self.send_command_to_2182A(query)
        time.sleep(QUERY_DELAY)
        return self.instrument.query(':SYST:COMM:SER:ENT?')

    def log_message(self, message):
        # This method will be connected to the GUI's log_to_terminal method
        print(message)  # Default behavior is to print to console

    def read_errors(self):
        errors = []
        while True:
            error = self.instrument.query(':SYST:ERR?')
            time.sleep(QUERY_DELAY)
            if error.startswith('0,'):  # No error
                break
            errors.append(error)
        return errors

    def run_pulsed_sweep(self, start, stop, num_pulses, sweep_type, voltage_range, 
                         pulse_width, pulse_delay, pulse_interval, voltage_compliance,
                         pulse_off_level, num_off_measurements, enable_compliance_abort):
        try:
            start_time = time.time()
            self.log_message("Starting pulsed sweep...")
            
            self.setup_pulsed_sweep(start, stop, num_pulses, sweep_type, voltage_range,
                                    pulse_width, pulse_delay, pulse_interval, voltage_compliance,
                                    pulse_off_level, num_off_measurements)
            self.set_compliance_abort(enable_compliance_abort)
            
            self.log_message("Setup complete. Arming instruments...")
            self.arm()
            
            arm_status = self.check_arm_status()
            self.log_message(f"Arm status: {arm_status}")
            
            self.log_message("Initiating sweep...")
            self.initiate()
            
            self.log_message("Sweep in progress...")
            time.sleep(num_pulses * float(pulse_interval) + 1)  # Estimate sweep time
            
            voltage, current = self.get_data()
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.log_message(f"Sweep completed successfully in {elapsed_time:.2f} seconds.")
            
            return voltage, current
        
        except Exception as e:
            self.log_message(f"An error occurred during the sweep: {str(e)}")
            self.abort()
            return None, None
        finally:
            errors = self.read_errors()
            if errors:
                self.log_message("Errors occurred during the sweep:")
                for error in errors:
                    self.log_message(error)
            else:
                self.log_message("No errors detected during the sweep.")

    def calc_data_delay(self):
        return ((self.stop - self.start) / self.step) * self.delay

    def set_sweep_type(self, sweep_type):
        if sweep_type.upper() == 'LINEAR':
            self.set_linear_staircase()
        else:
            self.set_logarithmic_staircase()
        time.sleep(SETUP_DELAY)

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
        