import pyvisa as visa
import time
import sys
import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import logging
import datetime

INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"
SLEEP_INTERVAL = 0.2
DEBUG_PRINT_COMMANDS = True

filename = 'pulsed_iv_sweep_data.csv'
logging.basicConfig(level=logging.DEBUG if DEBUG_PRINT_COMMANDS else logging.INFO)  # Configure logging level

class PulseIVSweep:
    def __init__(self):
        self.rm = visa.ResourceManager('@ivi')
        self.k6221 = self.rm.open_resource(INSTRUMENT_RESOURCE_STRING_6221)
        self.k6221.write_termination = '\n'
        self.k6221.read_termination = '\n'
        self.k6221.timeout = 60000
        self.configure_instruments()

    def configure_instruments(self):
        self.k6221.write('*RST')
        self.wait_for_completion()
        self.send_command('SYST:BEEP:STAT OFF')
        self.wait_for_completion()
        self.send_command('FORM:ELEM VOLT,CURR')
        self.wait_for_completion()
        self.configure_2182A()
        print("Instruments Configured Successfully.")

    def configure_2182A(self):
        self.send_command_to_2182A('*RST')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A('SYST:PRES')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A('*CLS')
        self.wait_for_completion_2182A()
        self.send_command(':SYST:COMM:SER:BAUD 19200')
        self.wait_for_completion()
        self.send_command_to_2182A(':INIT:CONT OFF')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':ABORT')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':SYST:BEEP:STAT OFF')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':REM')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':TRACE:CLEAR')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':trace:feed:control next')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':SENS:FUNC "VOLT:DC"')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':SENS:CHAN 1')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':SYST:AZER:STAT OFF')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':SENS:VOLT:CHAN1:LPAS:STAT OFF')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':SENS:VOLT:CHAN1:DFIL:STAT OFF')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':SENS:VOLT:DC:NPLC 0.01')
        self.wait_for_completion_2182A()    
        self.send_command_to_2182A(':SENS:VOLT:CHAN1:RANG 10')
        self.wait_for_completion_2182A()    
        self.send_command_to_2182A(':SENS:VOLT:RANG 1')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':FORM:ELEM READ')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':TRIG:COUN 1')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':SAMP:COUN 11')
        self.wait_for_completion_2182A()   
        self.send_command_to_2182A(':TRACE:POINts 11')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':TRIG:DEL 0')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':STATus:MEASurement:ENABle 512; *SRE 1')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':TRACE:FEED sense1; :TRACE:FEED:CONTrol NEXT')
        self.wait_for_completion_2182A()
        self.send_command_to_2182A(':TRIG:SOUR IMM')

    def send_command(self, command):
        self.k6221.write(command)

    def send_command_to_2182A(self, command):
        self.send_command(f'SYST:COMM:SER:SEND "{command}"')

    def query_command(self, command):
        return self.k6221.query(command)

    def query_command_to_2182A(self, command):
        self.send_command_to_2182A(command)
        return self.query_command('SYST:COMM:SER:ENT?').strip()

    def wait_for_completion(self):
        self.send_command('*OPC')
        while True:
            response = self.query_command('*OPC?').strip()
            if response == '1':
                break
            time.sleep(SLEEP_INTERVAL)

    def wait_for_completion_2182A(self):
        self.send_command_to_2182A('*OPC')
        retries = 0
        while retries < 10:
            self.send_command_to_2182A('*OPC?')
            time.sleep(0.05)
            response = self.query_command('SYST:COMM:SER:ENT?').strip()
            if response == '1':
                break
            time.sleep(SLEEP_INTERVAL)
            retries += 1
        if retries == 10:
            print("Failed to get OPC response from 2182A")

    def setup_pulse(self):
        self.send_command('SOURce:SWEep:SPACing LIN')
        self.wait_for_completion()
        self.send_command('SOURce:CURRent:STARt 0')
        self.send_command('SOURce:CURRent:STOP 0.01')
        self.send_command('SOURce:CURRent:STEP 0.001')
        self.wait_for_completion()
        self.send_command('SOUR:PDEL:HIGH 0.01')
        self.wait_for_completion()
        self.send_command('SOUR:PDEL:LOW 0')
        self.wait_for_completion()
        self.send_command('SOUR:PDEL:WIDTh 500e-9')
        self.wait_for_completion()
        self.send_command('SOUR:PDEL:SDEL 500e-9')
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:INTerval 1e-6')
        self.wait_for_completion()
        self.send_command('SOUR:PDEL:RANG BEST')
        self.wait_for_completion()
        self.send_command('SOUR:PDEL:INT 5')
        self.wait_for_completion()
        self.send_command('SOUR:PDEL:LME 2')
        self.wait_for_completion()
        self.send_command('SOUR:PDEL:SWE ON')
        self.send_command('SOUR:PDEL:ARM')
        self.wait_for_completion()

    def perform_sweep(self):
        self.send_command_to_2182A(':INIT:IMM')
        self.send_command('INITiate:IMMediate')
        time.sleep(5)
        self.send_command('SOUR:SWE:ABORT')
        self.wait_for_completion()
        self.send_command_to_2182A('ABORT')
        self.wait_for_completion_2182A()
        time.sleep(5)



    def fetch_existing_data(self):
        voltages = self.query_command_to_2182A('trac:data?').strip().strip('[]')
        if not voltages:
            print("No data returned from 2182A.")
            return []
        return [float(v) for v in voltages.split(',') if v]

    def fetch_data_6221(self):
        raw_data = self.query_command('trac:data?').strip()
        if not raw_data:
            print("No data returned from 6221.")
            return []
        return [float(v) for v in raw_data.split(',') if v]

    def user_check(self):
        user_response = input("Do you want to continue with the pulse sweep? (yes/no): ").strip().lower()
        if user_response not in ['yes', 'no']:
            print("Invalid response. Please enter 'yes' or 'no'.")
            return self.user_check()
        elif user_response == 'no':
            print("Discontinuing program...")
            return self.abort_sweep()
        elif user_response == 'yes':
            print("Continuing with pulse sweep...")
            return True
        else:
            return False

    def abort_sweep(self):
        print("Aborting pulse sweep...")
        self.send_command('SOUR:SWE:ABORT')
        self.wait_for_completion()
        self.send_command_to_2182A('ABORT')
        self.wait_for_completion_2182A()
        print("Pulse sweep aborted.")
        self.k6221.close()
        self.rm.close()
        sys.exit(1)

    def run(self):
        self.setup_pulse()
        self.user_check()
        self.perform_sweep()
        self.send_command('SOUR:SWE:ABORT')
        self.wait_for_completion()
        self.send_command_to_2182A('ABORT')
        self.wait_for_completion_2182A()
        voltages = self.fetch_existing_data()
        #for i, voltage in enumerate(voltages):
        #    print(f"Stored Measurement {i+1}: {voltage} V")
        currents = [0 + x * (0.01 - 0) / 10 for x in range(11)]
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Current (A)', 'Voltage (V)', 'Resistance (Ohms)'])
            for current, voltage in zip(currents, voltages):
                resistance = voltage / current if current != 0 else 0
                writer.writerow([current, voltage, resistance])
                print(f'Current: {current}, Voltage: {voltage}, Resistance: {resistance}')

    def live_plot(self):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        plt.style.use('ggplot')

        def animate(i):
            data = pd.read_csv(filename)
            x = data['Current (A)']
            y = data['Voltage (V)']
            z = data['Resistance (Ohms)']
            ax1.cla()
            ax2.cla()
            ax1.plot(x, y, marker='o', label='I-V')
            ax2.plot(x, z, marker='*', label='I-R')
            ax1.set_xlabel('Current (A)')
            ax1.set_ylabel('Voltage (V)')
            ax2.set_xlabel('Current (A)')
            ax2.set_ylabel('Resistance (Ohms)')
            ax1.legend()
            ax2.legend()

        ani = FuncAnimation(fig, animate, interval=1000)
        plt.show()

if __name__ == "__main__":
    sweep = PulseIVSweep()
    sweep.run()
    voltages = sweep.fetch_existing_data()
    for i, voltage in enumerate(voltages):
        print(f"Stored Measurement {i+1}: {voltage} V")
    
    try:
        data_6221 = sweep.fetch_data_6221()
        for p, value in enumerate(data_6221):
            print(f"6221 Stored Measurement {p+1}: {value}")
    except ValueError as e:
        print(f"Error reading 6221 data: {e}")
    sweep.user_check()
    sweep.live_plot()
    print('Pulsed IV Sweep Completed')
