import sys
import os
import csv
import time
import pyvisa as visa
import argparse

DEBUG_PRINT_COMMANDS = True
INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"
INSTRUMENT_RESOURCE_STRING_2182A = "GPIB0::7::INSTR"
DATA_FILENAME = "pulse_sweep_data.csv"

class BroomK6221:
    def __init__(self):
        self.K6221Address = INSTRUMENT_RESOURCE_STRING_6221
        self.rm = visa.ResourceManager()
        self.k6 = self.rm.open_resource(self.K6221Address, write_termination='\n', read_termination='\n')
        self.k6.timeout = 60000  # Increased timeout
        self.init_instrument()
    
    def init_instrument(self):
        self.send_command('SYST:PRES')
        self.wait_for_completion()
        self.send_command('SOUR:SWE:ABORT')
        self.wait_for_completion()
        #self.send_command('SYST:BAUD 9600')
        #self.wait_for_completion()
        self.send_command('SYST:COMM:SER:SEND ":SYST:PRES"')
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND ":ABORT"')
        self.wait_for_completion_2182A()
        self.send_command('FORM:ELEM READ,TST,RNUM,SOUR')
        self.wait_for_completion()
        print("Configured Successfully.")

    def send_command(self, command):
        if DEBUG_PRINT_COMMANDS:
            print(f"Sending command: {command}")
        self.k6.write(command)

    def query_command(self, command):
        if DEBUG_PRINT_COMMANDS:
            print(f'Querying command: {command}')
        return self.k6.query(command)

    def wait_for_completion(self):
        self.send_command('*OPC')
        while self.query_command('*OPC?').strip() != '1':
            time.sleep(0.1)
        if DEBUG_PRINT_COMMANDS:
            print('K6221 Operation Complete.')

    def wait_for_completion_2182A(self):
        self.send_command('SYST:COMM:SER:SEND "*OPC"')
        response = ''
        while response.strip() != '1':
            self.send_command('SYST:COMM:SER:SEND "*OPC?"')
            time.sleep(0.05)
            response = self.query_command('SYST:COMM:SER:ENT?')
            if DEBUG_PRINT_COMMANDS:
                print(f'2182A OPC response: {response}')
            time.sleep(0.1)

    def configure_pulse_sweep(self):
        self.send_command(':SOUR:SWE:ABOR')
        self.wait_for_completion()
        self.send_command('*RST')
        self.wait_for_completion()
        #self.send_command(":SOUR:FUNC VOLT")
        #self.wait_for_completion()
        self.send_command('SOUR:PDEL:SWE ON')
        self.wait_for_completion()
        self.send_command('SOUR:DEL 0.006')
        self.wait_for_completion()
        self.send_command('SOUR:CURR:POIN 11')
        self.wait_for_completion()
        self.send_command('SOUR:SWE:SPAC LIN')
        self.wait_for_completion()
        self.send_command('SOUR:CURR:START 0')
        self.wait_for_completion()
        self.send_command('SOUR:CURR:STOP 0.01')
        self.wait_for_completion()
        #self.send_command('SOUR:PDEL:RANG BEST')
        #self.wait_for_completion()
        self.send_command('SOUR:SWE:RANG BEST')
        self.wait_for_completion()
        #self.send_command('SOUR:PDEL:WIDTH 0.1')
        #self.wait_for_completion()
        #self.send_command('SOUR:PDEL:SDEL 0.01')
        #self.wait_for_completion()
        self.send_command('SOUR:PDEL:LME 2')
        self.wait_for_completion()
        #self.send_command('SOUR:PDEL:INT 0.1')
        #self.wait_for_completion()
        #self.send_command('SOUR:CURR:COMP 0.1')
        #self.wait_for_completion()
        #self.send_command('SOUR:CURR:STEP 0.1')
        #self.wait_for_completion()
        self.send_command('SYST:COMM:SER:SEND ":SENS:VOLT:RANG 10"')
        self.wait_for_completion_2182A()
        self.send_command('SENS:AVER:WIND 0')
        self.wait_for_completion()
        self.send_command('SENS:AVER:STAT OFF')
        self.wait_for_completion()
        self.send_command('SENS:AVER:COUN 0')
        self.wait_for_completion()
        #self.send_command('SENS:AVER:TCON MOV')
        #self.wait_for_completion()
        self.send_command('SOUR:PDEL:ARM')
        self.wait_for_completion()
        if not self.user_check():
            self.send_command(':SOUR:SWE:ABORT')
            self.wait_for_completion()
            print("Sweep aborted by user.")
            return False
        self.send_command(':INIT:IMM')
        self.wait_for_completion()
        return True

    def run_pulse_sweep(self):
        if self.configure_pulse_sweep():
            data_points = self.get_data_points()
            if data_points > 0:
                data = self.read_data(data_points)
                self.save_data(data)
            else:
                print("No data points available after sweep.")

    def get_data_points(self):
        response = self.query_command(':TRAC:POIN:ACT?').strip()
        return int(response) if response else 0

    def read_data(self, num_readings):
        data = []
        for i in range((num_readings - 1) // 1000 + 1):
            data_sel_count = 1000 if num_readings - i * 1000 > 1000 else num_readings - i * 1000
            raw_data = self.k6.query(f"TRAC:DATA:SEL? {i * 1000 + 1},{data_sel_count}")
            data.extend(raw_data.split(","))
        return data

    def save_data(self, data):
        with open(DATA_FILENAME, "w", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Voltage Reading", "Timestamp", "Source Current", "Reading Number"])
            for i in range(0, len(data), 4):
                writer.writerow(data[i:i+4])
        print(f"Data saved to {DATA_FILENAME}")

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
    broom = BroomK6221()
    broom.parse_and_execute()
    broom.close()

if __name__ == "__main__":
    main()
    sys.exit(0)
