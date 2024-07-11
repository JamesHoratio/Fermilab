# sweep_functions2.py
import matplotlib.pyplot as plt
import pyvisa
import time
import numpy as np
from config import INSTRUMENT_ADDRESS, TIMEOUT, CONNECTION_SUCCESS, CONNECTION_ERROR
from sweep_functions import *
import csv
import datetime


date = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
class PulsedIVTest:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(INSTRUMENT_ADDRESS)
        self.instrument.timeout = TIMEOUT
        self.instrument.write_termination = '\n'
        self.instrument.read_termination = '\n'
        self.filename = f'IVSweep{date}.csv'

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
    
    def wait_for_operation_complete(self):
        self.instrument.query('*OPC?')
        time.sleep(QUERY_DELAY)

    def wait_for_operation_complete_2182A(self):
        self.query_2182A('*OPC?')
        time.sleep(QUERY_DELAY)

    def clear_buffers(self):
        self.instrument.write('*CLS')  # Clear status registers and error queue
        self.instrument.read()  # Read and discard any lingering output
        time.sleep(SETUP_DELAY)

    def send_command_to_2182A(self, command):
        self.instrument.write(f':SYST:COMM:SER:SEND "{command}"')
        time.sleep(SETUP_DELAY)

    def query_2182A(self, query):
        self.send_command_to_2182A(query)
        time.sleep(QUERY_DELAY)
        return self.robust_query(':SYST:COMM:SER:ENT?')
    
    def clear_buffers_2182A(self):
        self.send_command_to_2182A('*CLS')
        self.query_2182A('*OPC?')
        time.sleep(SETUP_DELAY)

    def reset_6221(self):
        self.instrument.write('*RST')
        time.sleep(LONG_COMMAND_DELAY)
        self.wait_for_operation_complete()
        self.clear_buffers()
        self.log_message("6221 has been reset.")

    def log_message(self, message):
        print(message)  # Default behavior is to print to console

    def verify_instrument_identity(self):
        idn = self.robust_query('*IDN?')
        if '6221' not in idn:
            raise Exception("Connected to wrong instrument or communication error")

    def setup_sweep(self):
        self.instrument.write('*RST')
        time.sleep(3)  # Wait for reset to complete
        self.instrument.write(':FORM:ELEM READ,SOUR') # Set data format to read both voltage and current
        time.sleep(0.1)
        self.instrument.write(':SOUR:CURR:STAR 0') # sets the start level of the current sweep
        time.sleep(0.1)
        qstartlevel = self.instrument.query(':SOUR:CURR:STAR?') # query the start level of the current sweep
        print(f'Start Level: {qstartlevel}')
        time.sleep(0.1)
        self.instrument.write(':SOUR:CURR:STOP 10e-3') # sets the stop level of the current sweep
        time.sleep(0.1)
        qstoplevel = self.instrument.query(':SOUR:CURR:STOP?')
        print(f'Stop Level: {qstoplevel}')
        time.sleep(0.1)
        self.instrument.write(':SOUR:SWE:SPAC LIN') # sets sweep type, either linear or logarithmic
        time.sleep(0.1)
        qsweeptype = self.instrument.query(':SOUR:SWE:SPAC?') # query the sweep type
        print(f'Sweep Type: {qsweeptype}')
        time.sleep(0.1)
        self.instrument.write('SOUR:CURR:POIN 11') # sets the number of points in the sweep
        time.sleep(0.1)
        qnum_points = self.instrument.query(':SOUR:CURR:POIN?') # query the number of points in the sweep
        print(f'Number of Points in Sweep: {qnum_points}')
        time.sleep(0.1)
        self.instrument.write('SOUR:CURR ')
        self.instrument.write(':SOUR:PDEL:COUN 11') # sets the number of pulses to be generated or pulse count
        time.sleep(0.1)
        qnum_pulses = self.instrument.query(':SOUR:PDEL:COUN?') # query the number of pulses
        print(f'Number of Pulses: {qnum_pulses}')
        time.sleep(0.1)
        self.instrument.write(':SOUR:PDEL:SWE ON') # turn on sweep mode for pulse delta measurements
        time.sleep(3)
        qsweep = self.instrument.query(':SOUR:PDEL:SWE?') # query the sweep mode
        print(f'Sweep Mode: {qsweep}')
        time.sleep(0.1)
        self.instrument.write(':SOUR:DEL 0.001')  # set the delay between pulses (the time between the end of one pulse and the start of the next) the lowest it can be set is 0.001 ms
        time.sleep(0.3)
        qdelay = self.instrument.query(':SOUR:DEL?') # query the delay between pulses
        print(f'Delay: {qdelay}')
        time.sleep(0.1)
        
    def clean_buffer(self):
        self.instrument.write('TRAC:CLE')
        time.sleep(SETUP_DELAY)
    
    def set_buffer_size(self, size=DEFAULT_BUFFER_SIZE):
        self.instrument.write(f'TRAC:POIN {size}')
        time.sleep(SETUP_DELAY)

    def setup_trigger_link(self):
        self.instrument.write(':TRIG:SOUR TLINK') # set the trigger source to be the trigger link
        time.sleep(0.1)
        self.instrument.write(':SOUR:EXTR:ILIN 1') # set trigger link line #1 to be the external trigger
        time.sleep(0.1)
        self.instrument.write(':SOUR:EXTR:ENABLE ON')

    def setup_immediate_trigger(self):
        self.instrument.write(':SOUR:EXTR:ENABLE OFF') # turn off external trigger
        time.sleep(0.1)
        self.instrument.write(':TRIG:SOUR IMM') # set the trigger source to be immediate
        time.sleep(0.1)
        

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

    def abort_sweep(self):
        self.instrument.write(':SOUR:SWE:ABOR')
        time.sleep(4)
    
    def arm_sweep(self):
        self.instrument.write(':SOUR:PDEL:ARM')
        time.sleep(5)

    def print_data(self):
        voltage, current = self.get_data()
        for v, i in zip(voltage, current):
            print(f'Voltage: {v}, Current: {i}')
    
    def read_errors(self):
        errors = []
        while True:
            error = self.robust_query(':SYST:ERR?')
            if error.startswith('0,'):  # No error
                break
            errors.append(error)
        return errors
    
    def graph_data(self):
        voltage, current = self.get_data()
        # Plot the data here
        with open(f'{self.filename}', 'a', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(['Voltage (V)', 'Current (A)'])
            for v, i in zip(voltage, current):
                writer.writerow([v, i])
            f.close()
        color = ('#004C97')

        plt.title('Pulsed IV Sweep')
        plt.xlabel('Current (A)')
        plt.ylabel('Voltage (V)')
        plt.plot(current, voltage, c=color, label=(f'Pulsed IV Sweep {date}'))
        plt.show()
    

def main():
    test = PulsedIVTest()
    test.setup_sweep()
    #test.setup_immediate_trigger()
    #test.setup_trigger_link()
    test.arm_sweep()
    test.run_measurement()
    test.abort_sweep()
    test.print_data()
    test.graph_data()
    test.close()

# Usage example
if __name__ == '__main__':
    main()