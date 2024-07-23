# sweep_functions2.py
import matplotlib.pyplot as plt
import pyvisa
import time
import numpy as np
from config import INSTRUMENT_ADDRESS, TIMEOUT, CONNECTION_SUCCESS, CONNECTION_ERROR
from sweep_functions import *
import csv
import datetime
import re
import sys

voltage = []
current = []
timestamp = []

date = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
class BaseSweep:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.instrument = None
        self.filename = f'Sweep_{date}.csv'

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
        except Exception as e:
            self.log_message(f"Unexpected error during connection: {str(e)}")
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

    def clean_buffer(self):
        self.instrument.write('TRAC:CLE')
        time.sleep(SETUP_DELAY)
    
    def set_buffer_size(self, size=DEFAULT_BUFFER_SIZE):
        self.instrument.write(f'TRAC:POIN {size}')
        time.sleep(SETUP_DELAY)

    def close(self):
        self.instrument.close()
        self.rm.close()

    def abort_sweep(self):
        self.instrument.write(':SOUR:SWE:ABOR')
        time.sleep(4)

    def read_errors(self):
        errors = []
        while True:
            error = self.robust_query(':SYST:ERR?')
            if error.startswith('0,'):  # No error
                break
            errors.append(error)
        return errors
    
    def query_command(self, command):
        return self.instrument.query(command)
    
    def fetch_data_6221(self):
        raw_data = self.query_command('trac:data?').strip()
        data = raw_data.split(',')
        return [float(v) for v in data if v]  # Only convert non-empty strings to float

        #voltage = newdata[0::3]
        #timestamp = data[1::3]
        #current = data[2::3]
        #return np.array(voltage), np.array(timestamp), np.array(current)

    
    
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
        except Exception as e:
            self.log_message(f"Unexpected error during connection: {str(e)}")
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

    def clean_buffer(self):
        self.instrument.write('TRAC:CLE')
        time.sleep(SETUP_DELAY)
    
    def set_buffer_size(self, size=DEFAULT_BUFFER_SIZE):
        self.instrument.write(f'TRAC:POIN {size}')
        time.sleep(SETUP_DELAY)

    def close(self):
        self.instrument.close()
        self.rm.close()

    def abort_sweep(self):
        self.instrument.write(':SOUR:SWE:ABOR')
        time.sleep(4)

    def read_errors(self):
        errors = []
        while True:
            error = self.robust_query(':SYST:ERR?')
            if error.startswith('0,'):  # No error
                break
            errors.append(error)
        return errors
    
    def query_command(self, command):
        return self.instrument.query(command)
    
    def fetch_data_6221(self):
        raw_data = self.query_command('trac:data?').strip()
        data = raw_data.split(',')
        return [float(v) for v in data if v]  # Only convert non-empty strings to float

        #voltage = newdata[0::3]
        #timestamp = data[1::3]
        #current = data[2::3]
        #return np.array(voltage), np.array(timestamp), np.array(current)

    def setup_sweep(self):
        self.instrument.write('*RST')
        time.sleep(0.5)  # Wait for reset to complete
        self.instrument.write('pdel:high 0.01') # set the high level to 10mA
        time.sleep(0.1)
        self.instrument.write('pdel:coun INF') # set the pulse count to infinite
        time.sleep(0.1)
        self.instrument.write('pdel:widt 0.0001') # set the pulse width to 100us
        time.sleep(0.1)
        self.instrument.write('pdel:sdel 6e-5') # set the pulse delay to 60us
        time.sleep(0.1)
        self.instrument.write('pdel:int 5') # set the pulse interval to 5ms
        time.sleep(0.1)
        self.instrument.write(':syst:comm:ser:send ":sens:volt:rang 0.01"') # set 2182A to 10mV range for best sensitivity on the 5mV expected signal
        time.sleep(0.1)
        self.instrument.write('pdel:swe on') # turn on the pulse delta sweep mode
        time.sleep(0.1)
        self.instrument.write('swe:spac lin') # set the sweep spacing to linear
        time.sleep(0.1)
        self.instrument.write('curr:start 0') # set the start current to 0A
        time.sleep(0.1)
        self.instrument.write('curr:stop 0.01') # set the stop current to 10mA
        time.sleep(0.1)
        self.instrument.write('curr:step 0.001') # set the current step to 1mA
        time.sleep(0.1)
        self.instrument.write('sour:del 0.001') # set the delay between pulses to 1ms
        time.sleep(0.1)
        self.instrument.write('sour:curr:comp 100') # set the current compliance to 100V
        time.sleep(0.1)
        self.instrument.write('sour:swe:cab off')
        time.sleep(0.1)
        self.instrument.write('swe:rang best') # set the source range to best
        time.sleep(0.1)
        self.instrument.write('SYST:COMM:SERIal:SEND ":sens:volt:rang 0.1"') # set 2182A to 100mV range for best sensitivity on the 5mV expected signal
        time.sleep(0.3)
        #self.instrument.write('SYST:COMM:SERIal:SEND "curr:comp 100"')
        #time.sleep(0.3)
        self.instrument.write('form:elem read,sour,tst') # set the data format to read both voltage and current
        time.sleep(3)
    
    def verify_sweep_setup(self):
        qhigh = self.instrument.query('pdel:high?')
        qlow = self.instrument.query('pdel:low?')
        qcount = self.instrument.query('pdel:coun?')
        qwidth = self.instrument.query('pdel:widt?')
        qsdel = self.instrument.query('pdel:sdel?')
        qint = self.instrument.query('pdel:int?')
        qrange = self.instrument.query('swe:rang?')
        qstart = self.instrument.query('curr:start?')
        qstop = self.instrument.query('curr:stop?')
        qpoints = self.instrument.query('sour:swe:poin?')
        qdelay = self.instrument.query('sour:del?')
        qformat = self.instrument.query(':form:elem?')
        qcab = self.instrument.query('sour:swe:cab?')
        qtrig = self.instrument.query('trig:sour?')
        qdir = self.instrument.query('trig:dir?')
        qolin = self.instrument.query('trig:olin?')
        qilin = self.instrument.query('trig:ilin?')
        qoutp = self.instrument.query('trig:outp?')
        print(f'High: {qhigh}')
        print(f'Low: {qlow}')
        print(f'Count: {qcount}')
        print(f'Width: {qwidth}')
        print(f'Sdel: {qsdel}')
        print(f'Int: {qint}')
        print(f'Range: {qrange}')
        print(f'Start: {qstart}')
        print(f'Stop: {qstop}')
        print(f'Sweep Points: {qpoints}')
        print(f'Delay: {qdelay}')
        print(f'Format: {qformat}')
        print(f'Cab: {qcab}')
        print(f'Trig: {qtrig}')
        print(f'Dir: {qdir}')
        print(f'Olin: {qolin}')
        print(f'Ilin: {qilin}')
        print(f'Outp: {qoutp}')

    def setup_trigger_link(self):
        self.instrument.write('*RST')
        time.sleep(0.5)  # Wait for reset to complete
        self.instrument.write(':TRIG:CLE') # clear the trigger link
        time.sleep(0.1)
        self.instrument.write('ARM:DIR ACC') # set the arm direction to accept
        time.sleep(0.1)
        self.instrument.write('ARM:COUN 1') # perform 1 scan
        time.sleep(0.1)
        self.instrument.write('ARM:SOUR IMM') # immediately go to next layer
        time.sleep(0.1)
        #self.instrument.write('arm:outp none')
        self.instrument.write('TRIG:DIR ACC') # set the trigger direction to accept
        time.sleep(0.1)
        self.instrument.write('TRIG:COUN 1') # perform 1 scan
        time.sleep(0.1)
        self.instrument.write(':TRIG:SOUR TLIN') # set the trigger source to be the trigger link
        time.sleep(0.1)
        self.instrument.write(':TRIG:OUTP SOUR') # output trigger after source
        time.sleep(0.1)
        self.instrument.write(':TRIG:ILIN 1') # set trigger link line #1 to be the external trigger
        time.sleep(0.1)
        # enable external trigger

    def setup_immediate_trigger(self):
        self.instrument.write(':SOUR:EXTR:ENABLE OFF') # turn off external trigger
        time.sleep(0.1)
        self.instrument.write(':TRIG:SOUR IMM') # set the trigger source to be immediate
        time.sleep(0.1)

    def arm_sweep(self):
        self.instrument.write(':SOUR:PDEL:ARM')
        time.sleep(5)

    def run_measurement(self):
        self.instrument.write(':INIT:IMM')
        time.sleep(5)  # Wait for measurement to complete
        
    def get_data(self):
        data = self.instrument.query_ascii_values(':TRAC:DATA?')
        voltage = data[0::3]
        timestamp = data[1::3]
        current = data[2::3]
        return np.array(voltage), np.array(timestamp), np.array(current)
    
    def print_data(self):
        voltage, timestamp, current = self.get_data()
        for v, t, i in zip(voltage, timestamp, current):
            print(f'Voltage: {v}, Timestamp: {t}, Current: {i}')
    
    def graph_data(self):
        voltage, timestamp, current = self.get_data()
        # Plot the data here
        with open(f'{self.filename}', 'a', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(['Voltage (V)', 'Current (A)', 'Timestamp (s)'])
            for v, i, t in zip(voltage, current, timestamp):
                writer.writerow([v, i, t])
            f.close()
        color = ('#004C97')

        plt.title('Pulsed IV Sweep')
        plt.xlabel('Current (A)')
        plt.ylabel('Voltage (V)')
        plt.plot(current, voltage, c=color, label=(f'Pulsed IV Sweep {date}'))
        plt.show()
    
    def runIVPulsed(self):
        base = BaseSweep()
        self.setup_sweep()
        self.verify_sweep_setup
        self.arm_sweep()
        self.run_measurement()
        base.abort_sweep()
        self.print_data()
        self.graph_data()
        base.close()


class DCSweep:

    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(INSTRUMENT_ADDRESS)
        self.instrument.write_termination = '\n'
        self.instrument.read_termination = '\n'
        self.instrument.timeout = TIMEOUT
        self.filename = f'DCSweep_{date}.csv'

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
        except Exception as e:
            self.log_message(f"Unexpected error during connection: {str(e)}")
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

    def clean_buffer(self):
        self.instrument.write('TRAC:CLE')
        time.sleep(SETUP_DELAY)
    
    def set_buffer_size(self, size=DEFAULT_BUFFER_SIZE):
        self.instrument.write(f'TRAC:POIN {size}')
        time.sleep(SETUP_DELAY)

    def close(self):
        self.instrument.close()
        self.rm.close()

    def abort_sweep(self):
        self.instrument.write(':SOUR:SWE:ABOR')
        time.sleep(4)

    def read_errors(self):
        errors = []
        while True:
            error = self.robust_query(':SYST:ERR?')
            if error.startswith('0,'):  # No error
                break
            errors.append(error)
        return errors
    
    def query_command(self, command):
        return self.instrument.query(command)
    
    def fetch_data_6221(self):
        raw_data = self.query_command('trac:data?').strip()
        data = raw_data.split(',')
        return [float(v) for v in data if v]  # Only convert non-empty strings to float

        #voltage = newdata[0::3]
        #timestamp = data[1::3]
        #current = data[2::3]
        #return np.array(voltage), np.array(timestamp), np.array(current)

    def armDCSweep(self):
        self.instrument.write(':sour:swe:arm')
        print('Arming DC Sweep... \nStarting in 4 seconds...') 
        time.sleep(1)
        print('Starting in 3 seconds...')
        time.sleep(1)
        print('Starting in 2 seconds...')
        time.sleep(1)
        print('Starting in 1 second...')
        time.sleep(1)
        print('Starting DC Sweep...')

    def runDCSweep(self):
        self.instrument.write(':init:imm')
        self.instrument.write(':SYST:COMM:SERIal:SEND "init"') #
        print('Starting DC Sweep... \n')
        time.sleep(5)
        self.instrument.write('sour:swe:abor')
        print('DC Sweep Complete... Aborting\n')
        time.sleep(0.1)

    def setupDCSweep(self):
        self.instrument.write('sour:swe:abort') # abort any existing sweeps
        time.sleep(0.1)
        print('Setting up DC Sweep... 1')
        self.instrument.write('*rst')
        time.sleep(2)
        print('Setting up DC Sweep... 2')
        #self.instrument.write('trac:cle') # set the source function to current
        #time.sleep(2)
        #self.instrument.write('form:elem read,tst,sour') # set the data format to read both voltage and current
        #time.sleep(4)
        self.instrument.write('SYST:COMM:SERIal:SEND "*RST"') # reset the 2182A
        time.sleep(2)
        self.instrument.write('SYST:COMM:SERIal:SEND "SYST:FFIL ON"') # turn on the fast filter
        time.sleep(2)
        print('Trying the format thing 2182A...')
        self.instrument.write('SYST:COMM:SERIal:SEND "form:elem read,tst"') # 
        time.sleep(2)
        print('Setting up DC Sweep... 3')
        self.instrument.write('OUTP:ISH OLOW')
        time.sleep(0.1)
        print('Setting up DC Sweep... 4')
        self.instrument.write('outp:lte OFF')
        time.sleep(1)
        print('Setting up DC Sweep... 5')
        #self.instrument.write('SYST:COMM:SERIal:SEND "*CLS"') # reset the 6221
        #time.sleep(2)
        #self.instrument.write('SYST:COMM:SERIal:SEND ":INIT:CONT OFF;:ABORT"') # reset the 6221
        #time.sleep(2)
        #self.instrument.write('SYST:COMM:SERIal:SEND ":TRAC:CLE"') # clear the buffer
        #time.sleep(2)
        #self.instrument.write('SYST:COMM:SERIal:SEND ":SENS:FUNC \'VOLT:DC\'"') #
        #time.sleep(2)
        self.instrument.write('sour:swe:rang best') # set the source range to best
        time.sleep(2)
        print('Setting up DC Sweep... 6')
        self.instrument.write('sour:swe:spac lin')
        time.sleep(2)
        print('Setting up DC Sweesp... 7')
        self.instrument.write('sour:swe:points 11')
        time.sleep(2)
        print('Setting up DC Sweep... 8')
        self.instrument.write('sour:swe:coun 1')
        time.sleep(2)
        print('Setting up DC Sweep... 9')
        self.instrument.write('sour:swe:cab off')
        time.sleep(2)
        print('Setting up DC Sweep... 10')
        self.instrument.write('sour:curr:start 0')
        time.sleep(2)
        print('Setting up DC Sweep... 11')
        self.instrument.write('sour:curr:stop 0.01')
        time.sleep(0.1)
        print('Setting up DC Sweep... 12')
        #self.instrument.write('sour:curr:step 0.001')
        #time.sleep(0.1)
        self.instrument.write('sour:curr:comp 100')
        #self.instrument.write('sour:list:curr 0,1e-3,0,2e-3,0,3e-3,0,4e-3,0,5e-3,0,6e-3,0,7e-3,0,8e-3,0,9e-3,0,10e-3') # set the current list
        #time.sleep(0.1)
        #self.instrument.write('sour:list:del 0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001,0.001')
        #time.sleep(0.1)
        #self.instrument.write('sour:list:comp 100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100,100')
        #time.sleep(0.1)
        self.instrument.write('sour:del 0.001')
        time.sleep(0.1)
        self.instrument.write('trig:sour tlink')
        time.sleep(0.1)
        self.instrument.write('trig:dir sour')
        time.sleep(0.1)
        self.instrument.write('trig:olin 2')
        time.sleep(0.1)
        self.instrument.write('trig:ilin 1')
        time.sleep(0.1)
        self.instrument.write('trig:outp del')
        time.sleep(0.1)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":sens:volt:rang 10"') # set 2182A to 10mV range for best sensitivity on the 5mV expected signal
        time.sleep(0.4)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":sens:volt:nplc 0.01"') # set 2182A to 0.01 NPLC for faster measurements
        time.sleep(0.4)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:cle"') # clear the buffer
        time.sleep(0.4)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:feed sens"') # 
        time.sleep(0.2)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:poin 11"') # 
        time.sleep(0.2)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trig:sour ext"') # 
        time.sleep(0.4)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trig:coun 11"') # 
        time.sleep(0.4)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:feed:control next"') # 
        time.sleep(0.5)

    def verifyDCSweepSetup(self):
        qhigh = self.instrument.query('sour:curr:star?')
        qlow = self.instrument.query('sour:curr:stop?')
        qcount = self.instrument.query('sour:swe:coun?')
        qstep = self.instrument.query('sour:curr:step?')
        qdelay = self.instrument.query('sour:del?')
        qcomp = self.instrument.query('sour:curr:comp?')
        qrange = self.instrument.query('sour:swe:rang?')
        qpoints = self.instrument.query('sour:swe:poin?')
        qcab = self.instrument.query('sour:swe:cab?')
        qtrig = self.instrument.query('trig:sour?')
        qdir = self.instrument.query('trig:dir?')
        qolin = self.instrument.query('trig:olin?')
        qilin = self.instrument.query('trig:ilin?')
        qoutp = self.instrument.query('trig:outp?')
        self.instrument.write(':SYST:COMM:SERIal:SEND ":sens:volt:rang?"')
        time.sleep(0.2)
        qvolt = self.instrument.query(':SYST:COMM:SERIal:ENT?')
        time.sleep(0.2)
        self.instrument.query(':SYST:COMM:SERIal:SEND ":sens:volt:nplc?"')
        time.sleep(0.2)
        qnplc = self.instrument.query(':SYST:COMM:SERIal:ENT?')
        time.sleep(0.2)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:poin?"')
        time.sleep(0.2)
        qpoint = self.instrument.query(':SYST:COMM:SERIal:ENT?')
        time.sleep(0.2)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trig:sour?"')
        time.sleep(0.2)
        qtrigsource = self.instrument.query(':SYST:COMM:SERIal:ENT?')
        time.sleep(0.2)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trig:coun?"')
        time.sleep(0.2)
        qtrigcount = self.instrument.query(':SYST:COMM:SERIal:ENT?')
        time.sleep(0.1)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:feed:control?"')
        time.sleep(0.2)
        qfeedcontrol = self.instrument.query(':SYST:COMM:SERIal:ENT?')
        time.sleep(0.1)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:data?"')
        time.sleep(0.2)
        qdata = self.instrument.query(':SYST:COMM:SERIal:ENT?')
        print(f'High: {qhigh}')
        print(f'Low: {qlow}')
        print(f'Count: {qcount}')
        print(f'Step: {qstep}')
        print(f'Delay: {qdelay}')
        print(f'Comp: {qcomp}')
        print(f'Range: {qrange}')
        print(f'Points: {qpoints}')
        print(f'Cab: {qcab}')
        print(f'Trig: {qtrig}')
        print(f'Dir: {qdir}')
        print(f'Olin: {qolin}')
        print(f'Ilin: {qilin}')
        print(f'Outp: {qoutp}')
        print(f'Volt Range 2182A: {qvolt}')
        print(f'NPLC 2182A: {qnplc}')
        #print(f'Cle: {qcle}')
        #print(f'Feed: {qfeed}')
        print(f'Point 2182A: {qpoint}')
        print(f'Trig Source 2182A: {qtrigsource}')
        print(f'Trig Count 2182A: {qtrigcount}')
        print(f'Feed Control 2182A: {qfeedcontrol}')
        print(f'Data 2182A: {qdata}')

    def getDCData(self):
            current = [0,0.001,0.002,0.003,0.004,0.005,0.006,0.007,0.008,0.009,0.01]
            self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:data?"')
            time.sleep(0.2)
            data = str(self.instrument.query(':SYST:COMM:SERIal:ENT?'))
            #print(f'Data: {data}')
            newdata = []
            #datalist = re.findall(r"[-+]?\d*\.\d+|\d+", data)
            for number in data.split(','):
                newdata.append(float(number))

            #print(f'Newdata: {newdata}')
            voltage = newdata[0::2]
            timestamp = newdata[1::2]

            for v, t, c in zip(voltage, timestamp, current):
                print(f'Voltage: {v}, Timestamp: {t}, Current: {c}')

            return np.array(voltage), np.array(timestamp), np.array(current)
            #k6221data = self.fetch_data_6221()
            #print(f'6221 Data: {k6221data}')
            #new6221data = []
            #if len(k6221data) > 0:
            #    for number in k6221data.split(','):
            #        new6221data.append(float(number))
            #        print(f'New 6221 Data: {new6221data}')
            #else:
            #    print('No data from 6221')

    def meas_data(self):
        current = [0,0.001,0.002,0.003,0.004,0.005,0.006,0.007,0.008,0.009,0.01]
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:data?"')
        time.sleep(0.2)
        data = self.instrument.query_ascii_values(':SYST:COMM:SERIal:ENT?')
        #data = self.instrument.query_ascii_values(':TRAC:DATA?')
        voltage = data[::2]
        timestamp = data[1::2]
        return np.array(voltage), np.array(timestamp),np.array(current)

    def printDCData(self):
        voltage, timestamp, current = self.meas_data()
        time.sleep(1)
        for v, t, i in zip(voltage, timestamp, current):
            print(f'Voltage: {v}, Timestamp: {t}, Current: {i}')

    def graphDCData(self):
        voltage, timestamp, current = self.getDCData()
        # Plot the data here
        with open(f'{self.filename}', 'a', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(['Voltage (V)', 'Current (A)', 'Timestamp (s)'])
            for v, i, t in zip(voltage, current, timestamp):
                writer.writerow([v, i, t])
            f.close()
        color = ('#004C97')

        plt.title('DC Sweep')
        plt.xlabel('Current (A)')
        plt.ylabel('Voltage (V)')
        plt.plot(current, voltage, c=color, label=(f'DC Sweep {date}'))
        plt.show()

    def runDC(self):
        self.setupDCSweep()
        time.sleep(1)
        self.armDCSweep()
        time.sleep(2)
        #self.printDCData()
        #self.getDCData()
        self.graphDCData()
        self.close()



def main():
    sweep_type = input("Enter 'pulsed' for Pulsed IV Sweep or 'dc' for a linear staircase DC Sweep, or q to abort and quit: ").lower()
    bsweep = BaseSweep()
    
    if not bsweep.connect():
        print("Failed to connect to the instrument. Please check the connection and try again.")
        sys.exit(1)
    
    if sweep_type == 'pulsed':
        print('Running Pulsed IV Sweep...')
        psweep = PulsedIVTest()
        psweep.runIVPulsed()
        print('Pulsed IV Sweep Complete...')
    elif sweep_type == 'dc':
        print('Running DC Sweep...')
        dsweep = DCSweep()
        dsweep.runDC()
        print('DC Sweep Complete...')
    elif sweep_type == 'q':
        print('Aborting and quitting...')
        bsweep.abort_sweep()
        bsweep.close()
        print('Sweep Aborted and Program Closed...')
        sys.exit(0)
    else:
        print("Invalid sweep type. Please enter 'pulsed', 'dc', or 'q'.")
    
    bsweep.close()
    sys.exit(0)

# Usage example
if __name__ == '__main__':
    main()
