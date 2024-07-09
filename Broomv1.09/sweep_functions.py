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
        self.sweep_type = ''
        self.pulse_width = 0
        self.pulse_delay = 0
        self.pulse_interval = 0
        self.voltage_compliance = 0
        self.pulse_off_level = 0
        self.pulse_count = 0

    def connect(self):
        try:
            self.instrument = self.rm.open_resource(INSTRUMENT_ADDRESS)
            self.instrument.timeout = TIMEOUT
            self.instrument.write_termination = '\n'
            self.instrument.read_termination = '\n'
            self.verify_instrument_identity()
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

    def verify_instrument_identity(self):
        idn = self.robust_query('*IDN?')
        if '6221' not in idn:
            raise Exception("Connected to wrong instrument or communication error")

    def robust_query(self, query, retries=3, timeout=5):
        for attempt in range(retries):
            try:
                self.instrument.timeout = timeout * 1000  # timeout in milliseconds
                response = self.instrument.query(query).strip()
                time.sleep(QUERY_DELAY)
                if response:
                    return response
            except pyvisa.errors.VisaIOError:
                self.log_message(f"Timeout occurred. Retrying... (Attempt {attempt + 1})")
            time.sleep(0.5)
        raise Exception(f"Failed to get response for query: {query}")

    def robust_query_ascii_values(self, query, retries=3, timeout=10):
        for attempt in range(retries):
            try:
                self.instrument.timeout = timeout * 1000  # timeout in milliseconds
                response = self.instrument.query_ascii_values(query)
                time.sleep(QUERY_DELAY)
                if response:
                    return response
            except pyvisa.errors.VisaIOError:
                self.log_message(f"Timeout occurred. Retrying... (Attempt {attempt + 1})")
            time.sleep(0.5)
        raise Exception(f"Failed to get response for query: {query}")

    def clear_buffers(self):
        self.instrument.write('*CLS')  # Clear status registers and error queue
        self.instrument.read()  # Read and discard any lingering output
        time.sleep(SETUP_DELAY)

    def clear_buffers_2182A(self):
        self.send_command_to_2182A('*CLS')
        self.query_2182A('*OPC?')
        time.sleep(SETUP_DELAY)

    def wait_for_operation_complete(self):
        self.instrument.query('*OPC?')
        time.sleep(QUERY_DELAY)

    def wait_for_operation_complete_2182A(self):
        self.query_2182A('*OPC?')
        time.sleep(QUERY_DELAY)

    def reset_communication(self):
        self.instrument.close()
        time.sleep(1)
        self.instrument = self.rm.open_resource(INSTRUMENT_ADDRESS)
        self.instrument.timeout = TIMEOUT

    def reset_6221(self):
        self.instrument.write('*RST')
        time.sleep(LONG_COMMAND_DELAY)
        self.wait_for_operation_complete()
        self.clear_buffers()
        self.log_message("6221 has been reset.")

    def query_6221(self):
        response = self.robust_query('*IDN?')
        self.log_message(f"6221 query response: {response}")
        return response

    def reset_2182a(self):
        self.send_command_to_2182A('*RST')
        time.sleep(LONG_COMMAND_DELAY)
        self.wait_for_operation_complete_2182A()
        self.clear_buffers_2182A()
        self.log_message("2182A has been reset.")

    def query_2182a(self):
        response = self.query_2182A('*IDN?')
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
        actual_value = self.robust_query(query)
        
        # Check if the response is an error message
        if actual_value.startswith('0,'):
            self.log_message(f"{parameter_name} query returned: {actual_value}")
            return
        
        try:
            actual_float = float(actual_value)
            expected_float = float(expected_value)
            if abs(actual_float - expected_float) < 1e-6:  # Use a small tolerance for float comparison
                self.log_message(f"{parameter_name} verified: {actual_value}")
            else:
                self.log_message(f"Warning: {parameter_name} mismatch. Expected: {expected_value}, Actual: {actual_value}")
        except ValueError:
            self.log_message(f"Warning: Could not verify {parameter_name}. Received: {actual_value}")

    def arm(self):
        self.instrument.write(':SOUR:PDEL:ARM')
        time.sleep(SETUP_DELAY)
        self.log_message("Instrument armed.")

    def check_arm_status(self):
        status = self.robust_query(':SOUR:PDEL:ARM?')
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
        data = self.robust_query_ascii_values(':TRAC:DATA?')
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
        return self.robust_query(':SYST:COMM:SER:ENT?')

    def log_message(self, message):
        print(message)  # Default behavior is to print to console

    def read_errors(self):
        errors = []
        while True:
            error = self.robust_query(':SYST:ERR?')
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
        if sweep_type.upper() == 'LIN':
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
    