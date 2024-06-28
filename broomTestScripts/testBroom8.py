import sys
import csv
import time
import pyvisa as visa
import argparse
import numpy as np
import datetime

DEBUG_PRINT_COMMANDS = True
INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"
DATA_FILENAME = "pulse_sweep_data.csv"

class BroomK6221:
    def __init__(self):
        self.K6221Address = INSTRUMENT_RESOURCE_STRING_6221
        self.rm = visa.ResourceManager()
        self.k6 = self.rm.open_resource(self.K6221Address, write_termination='\n', read_termination='\n')
        self.k6.timeout = 60000
        self.k6.send_end = True
        self.init_instrument()

    def init_instrument(self):
        self.send_command('*RST')
        self.wait_for_completion()
        self.send_command('SOUR:SWE:ABORT')
        self.wait_for_completion()
        self.send_command('SYST:BEEP:STAT OFF')
        self.wait_for_completion()
        self.send_command('FORM:ELEM READ,TST,RNUM,SOUR;')
        time.sleep(4)
        self.wait_for_completion()
        self.send_command('SYST:COMM:SER:SEND ":INIT:CONT OFF;:ABORT"')
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND "*CLS"')
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND ":SYST:PRES"')
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND "*RST"')
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND "TRAC:CLE"')
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND ":SYST:BEEP:STAT OFF"')
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND ":SYST:REM"')
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND ":SENS:FUNC \'VOLT:DC\'"')
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND ":SENS:CHAN 1"')
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:BAUD 19200')
        self.wait_for_completion_2182A()
        print("Configured Successfully.")

    def send_command(self, command):
        if DEBUG_PRINT_COMMANDS:
            print(f"Sending command: {command}")
        self.k6.write(command)

    def query_command(self, command):
        if DEBUG_PRINT_COMMANDS:
            print(f'Querying command: {command}')
        return self.k6.query(command)

    def flush_buffer(self):
        try:
            self.k6.clear()
        except visa.VisaIOError:
            pass

    def wait_for_completion(self):
        self.send_command('*OPC')
        response = ''
        while response.strip() != '1':
            response = self.query_command('*OPC?')
            time.sleep(1)
            if DEBUG_PRINT_COMMANDS:
                print(f'K6221 OPC response: {response}.')

    def wait_for_completion_2182A(self):
        self.send_command('SYST:COMM:SER:SEND "*OPC"')
        response = ''
        while response.strip() != '1':
            self.send_command('SYST:COMM:SER:SEND "*OPC?"')
            time.sleep(0.05)
            response = self.query_command('SYST:COMM:SER:ENT?')
            if DEBUG_PRINT_COMMANDS:
                print(f'K2182A OPC response: {response}')
            time.sleep(1)

    def configure_pulse_sweep(self):
        self.send_command('*RST')
        self.wait_for_completion()
        self.send_command('TRACe:CLEar')
        self.wait_for_completion()
        if self.query_command('SOURce:PDELta:NVPResent?').strip() != '1':
            print("Error establishing connection with the 2182A.")
        time.sleep(1)
        self.send_command('SYST:BEEP:STAT OFF')
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:HIGH 0.01')
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:LOW 0')
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:COUNt 11')
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:WIDth 0.0001')
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:SDELay 6e-5')
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:INTerval 5')
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:RANGing BEST')
        self.wait_for_completion()
        self.send_command('SYST:COMM:SER:SEND ":SENS:VOLT:RANG 0.1"')
        self.wait_for_completion_2182A()
        self.send_command('SOURce:PDELta:SWEep:STATe ON')
        self.wait_for_completion()
        self.send_command('SOURce:SWEep:SPACing LIN')
        self.wait_for_completion()
        self.send_command('SOURce:CURRent:STARt 0')
        self.wait_for_completion()
        self.send_command('SOURce:CURRent:STOP 0.01')
        self.wait_for_completion()
        self.send_command('SOURce:CURRent:STEP 0.001')
        self.wait_for_completion()
        self.send_command('SOURce:DEL 0.001')
        self.wait_for_completion()
        self.send_command('SOUR:SWE:RANG BEST')
        self.wait_for_completion()
        self.send_command('SYST:COMM:SER:SEND ":trig:coun 1;:sour ext"')
        self.wait_for_completion()
        self.send_command('SYST:COMM:SER:SEND ":samp:coun 11"')
        self.send_command('SOUR:PDEL:ARM')
        self.send_command('SYST:COMM:SER:SEND ":PDEL:ARM"')
        
        
        if not self.user_check():
            self.send_command(':SOUR:SWE:ABORT')
            self.wait_for_completion()
            return False
        self.send_command('INIT:IMM;SYST:COMM:SER:SEND ":INIT:IMM"')
        
        time.sleep(5)
        self.send_command(':SOUR:SWE:ABORT')
        self.wait_for_completion()
        time.sleep(1)
        return True

    def run_pulse_sweep(self):
        if self.configure_pulse_sweep():
            data_points = self.get_data_points()
            if data_points > 0:
                data = self.read_data(data_points)
                self.write_csv(data)

    def get_data_points(self):
        response = self.query_command(':TRAC:POIN:ACT?').strip()
        return int(response) if response else 0

    def read_data(self, num_readings: int):
        data = []
        retries = 0
        while num_readings > 0 and retries < 10:
            self.send_command('SYST:COMM:SER:SEND ":DATA?"')
            time.sleep(1)  # Added sleep to allow the command to process
            chunk_data = self.query_command('SYST:COMM:SER:ENT?').split(',')
            if len(chunk_data) > 1:  # Check to ensure data was received
                data.extend(chunk_data)
                num_readings -= len(chunk_data) // 4  # Assuming 4 elements per reading
                retries = 0  # Reset retries if data is received
            else:
                retries += 1  # Increment retries if no data received
                print(f"Retry {retries}/10")
        return data

    def write_csv(self, data):
        csv_path = f"Pulse_Sweep_Data_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        with open(csv_path, "w", newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Reading", "Timestamp", "Source Current", "Reading Number"])
            for i in range(0, len(data), 4):
                csv_writer.writerow(data[i:i+4])
        print(f"Data saved to {csv_path}")

    def user_check(self):
        user_response = input("Do you want to continue with the pulse sweep? (yes/no): ").strip().lower()
        return user_response == 'yes'

    def parse_and_execute(self):
        parser = argparse.ArgumentParser(description="Broom vTEST")
        parser.add_argument('--run_pulse_sweep', action='store_true', help='Run pulse sweep')
        args = parser.parse_args()
        if args.run_pulse_sweep:
            self.run_pulse_sweep()

    def close(self):
        self.k6.close()
        self.rm.close()

def main():
    start_time = time.time()
    broom = BroomK6221()
    broom.parse_and_execute()
    stop_time = time.time()
    print("done")
    print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")
    broom.close()

if __name__ == "__main__":
    main()
    sys.exit(0)
