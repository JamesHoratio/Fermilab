# sweep_functions3.py

import pyvisa
import time
import numpy as np
from config import INSTRUMENT_ADDRESS, TIMEOUT, CONNECTION_SUCCESS, CONNECTION_ERROR, SETUP_DELAY, DEFAULT_BUFFER_SIZE
#from sweep_functions import *

class PulsedIVTest:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.instrument = self.rm.open_resource(INSTRUMENT_ADDRESS)
        self.instrument.timeout = TIMEOUT
        self.instrument.write_termination = '\n'
        self.instrument.read_termination = '\n'

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
        
    def setup_sweep(self, start_level, stop_level, num_pulses, delay, sdel, plc, pulsewidth, sweep_type='LIN') -> None:
        def check_error():
            error = self.instrument.query("SYST:ERR?")
            if error.startswith("+0"):
                return
            print(f"Instrument Error: {error}")

        self.instrument.write('*RST')
        time.sleep(3)  # Wait for reset to complete
        check_error()

        self.instrument.write(':FORM:ELEM READ,SOUR')
        time.sleep(0.1)
        check_error()

        self.instrument.write('TRAC:POIN 5000')
        time.sleep(0.1)
        qpoint = self.instrument.query("TRAC:POIN?")
        print(f'Buffer Size: {qpoint}')
        check_error()

        self.instrument.write(f':SOUR:CURR:STAR {start_level}')
        time.sleep(0.1)
        qstartlevel = self.instrument.query(':SOUR:CURR:STAR?')
        print(f'Start Level: {qstartlevel}')
        check_error()

        self.instrument.write(f':SOUR:CURR:STOP {stop_level}')
        time.sleep(0.1)
        qstoplevel = self.instrument.query(':SOUR:CURR:STOP?')
        print(f'Stop Level: {qstoplevel}')
        check_error()

        self.instrument.write(f':SOUR:SWE:SPAC {sweep_type}')
        time.sleep(0.1)
        qsweeptype = self.instrument.query(':SOUR:SWE:SPAC?')
        print(f'Sweep Type: {qsweeptype}')
        check_error()

        #self.instrument.write('SOUR:PDEL:HIGH ' + str(stop_level))
        #time.sleep(0.1)
        qhigh = self.instrument.query(':pdel:high?')
        print(f'PDelta High: {qhigh}')
        check_error()

        #self.instrument.write('SOUR:PDEL:LOW ' + str(start_level))
        #time.sleep(0.1)
        qlow = self.instrument.query('sour:pdel:low?')
        print(f'PDelta Low: {qlow}')
        check_error()

        #self.instrument.write(f':PDEL:WIDT 12e-5')
        #time.sleep(0.1)
        qpulsewitdth = self.instrument.query(':SOUR:PDEL:WIDT?')
        print('Pulse Width: ' + qpulsewitdth)
        check_error()

        #self.instrument.write(f'SOUR:PDEL:SDEL {sdel}')
        #time.sleep(0.1)
        qsdel = self.instrument.query('sour:pdel:sdel?')
        print(f'Pulse Source Delay: {qsdel}')
        check_error()

        #self.instrument.write(f':SOUR:PDEL:COUN {num_pulses}')
        #time.sleep(0.1)
        qnum_pulses = self.instrument.query(':SOUR:PDEL:COUN?')
        print(f'Number of Pulses: {qnum_pulses}')
        check_error()

        self.instrument.write('SOUR:SWE:SPAC LIN')

        self.instrument.write('CURR:POIN 11')

        self.instrument.write('SOUR:PDEL:RANG BEST')
        time.sleep(0.1)
        qrange = self.instrument.query('sour:pdel:rang?')
        print(f'Pulse Delta Range: {qrange}')
        check_error()

        #self.instrument.write(f':SOUR:PDEL:INT {plc}')
        #time.sleep(0.1)
        qinterval = self.instrument.query(':SOUR:PDEL:INT?')
        print(f'Interval Time: {qinterval}')
        check_error()

        self.instrument.write(':SOUR:PDEL:SWE ON')
        time.sleep(0.1)
        qsweep = self.instrument.query(':SOUR:PDEL:SWE?')
        print(f'Sweep Mode: {qsweep}')
        check_error()

        self.instrument.write(f':SOUR:DEL {delay}')
        time.sleep(0.1)
        qdelay = self.instrument.query(':SOUR:DEL?')
        print(f'Delay: {qdelay}')
        check_error()

        
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
        #self.instrument.write(':SOUR:EXTR:ENABLE OFF') # turn off external trigger
        #time.sleep(0.1)
        self.instrument.write(':TRIG:SOUR IMM') # set the trigger source to be immediate
        time.sleep(0.1)
        

    def run_measurement(self):
        self.instrument.write(':INIT:IMM')
        print("Measurement initiated")
        time.sleep(0.1)
        self.instrument.write('*TRG')
        print("Trigger sent")
        time.sleep(5)  # Wait for measurement to complete
        sweep_status = self.instrument.query(':STAT:OPER:COND?')
        print(f"Operation status after trigger: {sweep_status}")
        
    def get_data(self):
        data = self.instrument.query_ascii_values(':TRAC:DATA?')
        points = len(data) // 2
        print(f"Number of data points: {points}")
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
        time.sleep(1)
        arm_status = self.instrument.query(':SOUR:PDEL:ARM?')
        print(f"Arm status: {arm_status}")
        if arm_status.strip() != '1':
            print("Warning: Sweep not armed properly")

    def check_trigger_settings(self):
        trigger_source = self.instrument.query('TRIG:SOUR?')
        print(f"Trigger Source: {trigger_source.strip()}")
    
    def print_data(self):
        voltage, current = self.get_data()
        for v, i in zip(voltage, current):
            print(f'Voltage: {v}, Current: {i}')
    
    def check_buffer_status(self):
        buffer_points = self.instrument.query_ascii_values('TRAC:POIN:ACT?')[0]
        print(f"Active buffer points: {buffer_points}")
    
    def query_all_settings(self):
        settings = [
            ('START', ':SOUR:CURR:STAR?'),
            ('STOP', ':SOUR:CURR:STOP?'),
            ('POINTS', ':SOUR:SWE:POIN?'),
            ('SWEEP TYPE', ':SOUR:SWE:SPAC?'),
            ('PDELTA HIGH', 'SOUR:PDEL:HIGH?'),
            ('PDELTA LOW', 'SOUR:PDEL:LOW?'),
            ('PULSE WIDTH', ':SOUR:PDEL:WIDT?'),
            ('SOURCE DELAY', 'SOUR:PDEL:SDEL?'),
            ('PULSE COUNT', ':SOUR:PDEL:COUN?'),
            ('PULSE RANGE', 'SOUR:PDEL:RANG?'),
            ('INTERVAL', ':SOUR:PDEL:INT?'),
            ('SWEEP MODE', ':SOUR:PDEL:SWE?'),
            ('DELAY', ':SOUR:DEL?'),
        ]

        print("Current settings:")
        for name, query in settings:
            value = self.instrument.query(query)
            print(f"{name}: {value.strip()}")

    def verify_pdelta_config(self):
        pdelta_settings = [
            ('HIGH', 'SOUR:PDEL:HIGH?'),
            ('LOW', 'SOUR:PDEL:LOW?'),
            ('WIDTH', 'SOUR:PDEL:WIDT?'),
            ('SDEL', 'SOUR:PDEL:SDEL?'),
            ('COUNT', 'SOUR:PDEL:COUN?'),
            ('RANG', 'SOUR:PDEL:RANG?'),
            ('INT', 'SOUR:PDEL:INT?'),
            ('SWE', 'SOUR:PDEL:SWE?'),
        ]

        print("Pulse Delta configuration:")
        for name, command in pdelta_settings:
            value = self.instrument.query(command)
            print(f"{name}: {value.strip()}")


    
def main():
    test = PulsedIVTest()
    test.setup_sweep(0, 10e-3, 11, 0.001, 0.000016, 5, 101e-6, 'LIN')
    test.verify_pdelta_config()
    test.check_trigger_settings()
    test.setup_immediate_trigger()
    test.arm_sweep()
    time.sleep(2)
    test.run_measurement()
    time.sleep(5)
    test.check_buffer_status()
    test.abort_sweep()
    test.print_data()
    test.close()


# Usage example
if __name__ == '__main__':
    main()