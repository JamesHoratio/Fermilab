import pyvisa as visa
import time
import sys
import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import logging
import datetime
import re

date = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"
SLEEP_INTERVAL = 0.2
DEBUG_PRINT_COMMANDS = True

filename = 'pulsed_iv_sweep_data.csv'
logging.basicConfig(level=logging.DEBUG if DEBUG_PRINT_COMMANDS else logging.INFO)  # Configure logging level

class PulseIVSweep:
    def __init__(self) -> None:
        self.rm = visa.ResourceManager('@ivi')
        self.k6221 = self.rm.open_resource(INSTRUMENT_RESOURCE_STRING_6221)
        self.k6221.write_termination = '\n'
        self.k6221.read_termination = '\n'
        self.k6221.timeout = 60000
        self.configure_instruments()
        self.start = 0
        self.stop = 0.01
        self.step = 0.001
        self.delay = 0.000016
        self.U = []
        self.I = []
        self.filenumber = 0
        self.filename = f'BroomSweep{date}.csv'

    def configure_instruments(self):
        self.k6221.write('*RST')
        time.sleep(0.35)
        self.send_command('SYST:BEEP:STAT OFF')
        time.sleep(0.35)
        self.send_command('FORM:ELEM VOLT,CURR')
        time.sleep(0.35)
        self.configure_2182A()
        print("Instruments Configured Successfully.")

    def configure_2182A(self):
        self.send_command_to_2182A('*RST')
        time.sleep(3)
        self.send_command_to_2182A('SYST:PRES')
        time.sleep(3)
        self.send_command_to_2182A('*CLS')
        time.sleep(0.2)
        self.send_command(':SYST:COMM:SER:BAUD 19200')
        time.sleep(3)
        self.send_command_to_2182A(':INIT:CONT OFF')
        time.sleep(0.2)
        self.send_command_to_2182A(':ABORT')
        time.sleep(0.2)
        self.send_command_to_2182A(':SYST:BEEP:STAT OFF')
        time.sleep(0.2)
        self.send_command_to_2182A(':REM')
        time.sleep(0.2)
        self.send_command_to_2182A(':TRACE:CLEAR')
        time.sleep(0.2)
        self.send_command_to_2182A(':trace:feed:control next')
        time.sleep(0.2)
        self.send_command_to_2182A(':SENS:FUNC "VOLT:DC"')
        time.sleep(0.2)
        self.send_command_to_2182A(':SENS:CHAN 1')
        time.sleep(0.2)
        self.send_command_to_2182A(':SYST:AZER:STAT OFF')
        time.sleep(0.2)
        self.send_command_to_2182A(':SENS:VOLT:CHAN1:LPAS:STAT OFF')
        time.sleep(0.2)
        self.send_command_to_2182A(':SENS:VOLT:CHAN1:DFIL:STAT OFF')
        time.sleep(0.2)
        self.send_command_to_2182A(':SENS:VOLT:DC:NPLC 0.01')
        time.sleep(0.2)    
        self.send_command_to_2182A(':SENS:VOLT:CHAN1:RANG 10')
        time.sleep(0.2)    
        self.send_command_to_2182A(':SENS:VOLT:RANG 1')
        time.sleep(0.2)
        self.send_command_to_2182A(':FORM:ELEM READ')
        time.sleep(0.2)
        self.send_command_to_2182A(':TRIG:COUN 1')
        time.sleep(0.2)
        self.send_command_to_2182A(':SAMP:COUN 11')
        time.sleep(0.2)   
        self.send_command_to_2182A(':TRACE:POINts 1000')
        time.sleep(0.2)
        self.send_command_to_2182A(':TRIG:DEL 0')
        time.sleep(0.2)
        #self.send_command_to_2182A(':STATus:MEASurement:ENABle 512; *SRE 1')
        #time.sleep(0.2)
        #self.send_command_to_2182A(':TRACE:FEED sense1; :TRACE:FEED:CONTrol NEXT')
        time.sleep(0.2)
        self.send_command_to_2182A(':TRIG:SOUR IMM')

    def send_command(self, command):
        logging.debug(f'Sending command to 6221: {command}')
        self.k6221.write(command)

    def send_command_to_2182A(self, command):
        logging.debug(f'Sending command to 2182A: {command}')
        self.send_command(f'SYST:COMM:SER:SEND "{command}"')

    def query_command(self, command):
        logging.debug(f'Querying command to 6221: {command}')
        return self.k6221.query(command)

    def query_command_to_2182A(self, command):
        self.send_command_to_2182A(command)
        response = self.query_command('SYST:COMM:SER:ENT?').strip()
        logging.debug(f'Response from 2182A: {response}')
        return response

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

    def calcDataDelay(self) -> int:

        timeDelay = ((self.stop - self.start) / self.step) * self.delay
        return round(timeDelay)

    def setup_pulse(self):
        self.send_command('SOUR:DEL 0.000016')
        time.sleep(0.35)
        self.send_command('SOUR:PDEL:LOW 0')
        time.sleep(0.35)
        self.send_command('SOUR:PDEL:HIGH 0.01')
        time.sleep(0.35)
        self.send_command('SOURce:PDELta:INTerval 0.000001')
        time.sleep(0.35)
        self.send_command('SOUR:PDEL:INT 5')
        time.sleep(0.35)
        self.send_command('SOUR:PDEL:LME 2')
        time.sleep(0.35)
        self.send_command('SOUR:PDEL:WIDT 0.001')
        time.sleep(0.35)
        self.send_command('SOUR:PDEL:SDEL 0.001')
        time.sleep(0.35)
        self.send_command('SOUR:PDEL:SWE ON')
        time.sleep(0.35)
        self.send_command('SOURce:SWEep:SPACing LIN')
        time.sleep(0.45)
        self.send_command('SOUR:CURR:STAR 0')
        time.sleep(0.35)
        self.send_command('SOUR:CURR:STOP 0.01')
        time.sleep(0.35)
        self.send_command('SOUR:CURR:STEP 0.001')
        time.sleep(0.35)
        self.send_command('SOUR:PDEL:RANG BEST')
        time.sleep(0.35)
        self.send_command('SOUR:CURR:COMP 100')
        time.sleep(0.35)
        self.send_command('TRAC:CLE')
        time.sleep(0.35)
        self.send_command('TRAC:POIN 5000')
        time.sleep(3)

        
        
        self.send_command('SOUR:PDEL:ARM')
        time.sleep(4)
        armstatus = self.query_command('SOUR:PDEL:ARM?')
        print(f'Arm Status: {armstatus}')

        

    def perform_sweep(self):
        print("Performing sweep...")
        self.send_command('INIT:IMM')
        time.sleep(self.calcDataDelay() + 3)
        
        self.send_command('SOUR:SWE:ABOR')
        time.sleep(5)
        self.k6221.write('SYST:COMM:SER:SEND "TRAC:DATA?"')
        data = str(self.k6221.query('SYST:COMM:SER:ENT?')).strip().strip('[]')
        datalist = data.split(',')[::2]

        # Filter out non-numeric data
        datalist = re.findall(r"[-+]?\d*\.\d+|\d+", data)

        for number in datalist:
            self.U.append(float(number))

        self.I = [self.start + i * self.step for i in range(len(self.U))]

        time.sleep(7)

        #self.filenumber += 1
        #with open(f'{self.filename}', 'a', encoding="utf-8") as f:
        #    for u, i in zip(self.U, self.I):
        #        f.write("{:<25.13f}{:<25.13f}\n".format(u, i))
        #    f.close()
#
        #with open(f'{self.filename}', 'r', encoding="utf-8") as f:
        #    reader = csv.reader(f)
        #    data = list(reader)
        #    U = [float(i[0]) for i in data]
        #    I = [float(i[1]) for i in data]
        #    f.close()

        with open(f'{self.filename}', 'a', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(['Voltage (V)', 'Current (A)'])
            for u, i in zip(self.U, self.I):
                writer.writerow([u, i])
            f.close()
        color = ('#004C97')

        plt.title('Pulsed IV Sweep')
        plt.xlabel('Current (A)')
        plt.ylabel('Voltage (V)')
        plt.plot(self.I, self.U, c=color, label=f'Pulsed IV Sweep {date}')
        plt.show()

    
        print("Sweep completed.")

                
            
        #self.send_command_to_2182A('ABORT')
        #time.sleep(0.2)
        #self.send_command(':OUTP OFF')
        #self.query_command('*IDN?')
        #self.wait_for_completion()
        #self.send_command_to_2182A('*RST')
        #self.wait_for_completion_2182A()
        #time.sleep(0.35)
        #self.send_command_to_2182A('*CLS')
        #time.sleep(3)
        #self.query_command_to_2182A('*IDN?')
        #time.sleep(0.5)
        #self.query_command('SYST:COMM:SER:ENT?')
        #time.sleep(0.5)
        #self.query_command('SYST:COMM:SER:ENT?')
        #time.sleep(5)

    def fetch_existing_data(self):
        logging.debug("Fetching data from 2182A.")
        voltages = self.query_command_to_2182A('trac:data?').strip().strip('[]')
        logging.debug(f'Raw data from 2182A: {voltages}')
        if not voltages:
            print("No data returned from 2182A.")
            return []
        return [float(v) for v in voltages.split(',') if v]
    

    
    #def fetch_existing_data(self):
    #    voltages = self.query_command_to_2182A('trac:data?').strip().strip('[]')
    #    return [float(v) for v in voltages.split(',')]

    def fetch_data_6221(self):
        logging.debug("Fetching data from 6221.")
        raw_data = self.query_command('trac:data?').strip()
        logging.debug(f'Raw data from 6221: {raw_data}')
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
        self.send_command('SOUR:SWE:ABOR')
        time.sleep(0.35)
        self.send_command_to_2182A('ABORT')
        time.sleep(0.2)
        print("Pulse sweep aborted.")
        self.k6221.close()
        self.rm.close()
        sys.exit(1)

    def run(self):
        self.setup_pulse()
        self.user_check()
        self.perform_sweep()
        time.sleep(0.2)
        #voltages = self.fetch_existing_data()
        #currents = [0 + x * (0.01 - 0) / 10 for x in range(11)]
        #with open(filename, 'w', newline='') as file:
        #    writer = csv.writer(file)
        #    writer.writerow(['Current (A)', 'Voltage (V)', 'Resistance (Ohms)'])
        #    for current, voltage in zip(currents, voltages):
        #        resistance = voltage / current if current != 0 else 0
        #        writer.writerow([current, voltage, resistance])
        #        print(f'Current: {current}, Voltage: {voltage}, Resistance: {resistance}')

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
    #voltages = sweep.fetch_existing_data()
    #for i, voltage in enumerate(voltages):
    #    print(f"Stored Measurement {i+1}: {voltage} V")
    #
    #try:
    #    data_6221 = sweep.fetch_data_6221()
    #    for p, value in enumerate(data_6221):
    #        print(f"6221 Stored Measurement {p+1}: {value}")
    #except ValueError as e:
    #    print(f"Error reading 6221 data: {e}")
    #sweep.user_check()
    #sweep.live_plot()
    print('Pulsed IV Sweep Completed')
