import sys
import time
import pyvisa as visa
import argparse

DEBUG_PRINT_COMMANDS = True
INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"  # Change this to your instrument's resource string
INSTRUMENT_RESOURCE_STRING_2182A = "GPIB0::7::INSTR"  # Change this to your instrument's resource string

class BroomK6221:
    def __init__(self):
        self.K6221Address = INSTRUMENT_RESOURCE_STRING_6221
        self.connected = self.connect6221()
        try:
            self.k6.write_termination = '\n'
            self.k6.read_termination = '\n'
            self.k6.timeout = 60000  # Set timeout to 60 seconds
            self.k6.write('*RST')
            time.sleep(1)
            self.k6.write('SYST:PRES')
            time.sleep(1)
            self.k6.write('SOUR:SWE:ABORT')
            time.sleep(1)
            self.k6.write('SYST:COMM:SER:SEND "*RST"')
            time.sleep(2)
            self.k6.write('SYST:COMM:SER:SEND "ABORT"')
            time.sleep(1)
            print("K6221 Configured Successfully.")
        except Exception as e:
            print(f"Error in __init__ method {e}.")
            sys.exit(1)

    def connect6221(self):
        try:
            self.rm = visa.ResourceManager()
            self.k6 = self.rm.open_resource(self.K6221Address, write_termination='\n', read_termination='\n')
            connectmessage = self.k6.query('*IDN?')
            print("Connected Instrument ID:", connectmessage)
            self.k6.write('SYST:COMM:SER:SEND "*IDN?"')
            time.sleep(0.05)
            response = self.k6.query('SYST:COMM:SER:ENT?')
            print(f"Connected Instrument ID: {response}")
        except visa.VisaIOError as e:
            print(f"Error initializing instrument: {e}")
            sys.exit(1)

    def send_command(self, command: str):
        try:
            if DEBUG_PRINT_COMMANDS:
                print(f"Sending command: {command}")
            self.k6.write(command)
        except visa.VisaIOError as e:
            print(f"Error sending command '{command}': {e}")

    def query_command(self, command: str) -> str:
        response = ''
        try:
            if DEBUG_PRINT_COMMANDS:
                print(f'Querying command: {command}')
                response = self.k6.query(command)
                print(f'Response: {response}')
                return response
        except visa.VisaIOError as e:
            print(f'Error querying command {command}: {e}')
            return ""

    def writeK2182(self, command):
        try:
            self.k6.write(f'SYST:COMM:SER:SEND "{command}"')
        except Exception as e:
            print(f"Error writing to K2182: {e}")

    def queryK2182(self, query: str) -> str:
        try:
            print(f"Querying K2182: {query}")
            self.k6.write(f'SYST:COMM:SER:SEND "{query}"')
            time.sleep(0.2)
            response = self.k6.query('SYST:COMM:SER:ENT?')
            print(f"Response from K2182: {response}")
            return response
        except Exception as e:
            print(f"Error querying K2182: {e}")
            return ""

    def configure_pulse_sweep(self):
        try:
            self.send_command(':SOUR:SWE:ABOR')
            time.sleep(3)
            self.send_command('*RST')
            self.send_command(":SOUR:FUNC VOLT")
            time.sleep(0.5)
            self.send_command('SOUR:DEL 0.006')
            self.send_command('FORM:ELEM READ,TST,RNUM,SOUR')
            self.send_command('SOUR:PDEL:COUNT 10')
            self.send_command('SOUR:PDEL:RANG BEST')
            self.send_command('SOUR:SWE:RANG BEST')
            self.send_command('SOUR:PDEL:WIDTH 0.1')
            self.send_command('SOUR:PDEL:SDEL 0.01')
            self.send_command('SOUR:PDEL:SWE 1')
            self.send_command('SOUR:PDEL:LME 2')
            self.send_command('SOUR:PDEL:INT 0.1')
            self.send_command('SOUR:CURR:COMP 0.1')
            self.send_command('SOUR:SWE:SPAC LIN')
            self.send_command('SOUR:CURR:START 0')
            self.send_command('SOUR:CURR:STOP 1')
            self.send_command('SOUR:CURR:STEP 0.1')
            self.send_command('SYST:COMM:SER:SEND ":SENS:VOLT:RANG 10"')
            self.send_command('SENS:AVER:WIND 0')
            self.send_command('SENS:AVER:STAT 0')
            self.send_command('SENS:AVER:COUN 0')
            self.send_command('SENS:AVER:TCON 0')
            self.send_command('SOUR:PDEL:ARM')
            time.sleep(3)
            self.send_command(':INIT:IMM')
        except Exception as e:
            print(f"Error configuring pulse sweep: {e}")

    def run_pulse_sweep(self):
        self.configure_pulse_sweep()
        time.sleep(10)  # Ensure enough time for sweep to complete
        data_points = self.get_data_points()
        if data_points > 0:
            data = self.read_data(data_points)
            print(f"Pulse sweep data: {data}")
        else:
            print("No data points available after sweep.")

    def get_data_points(self):
        try:
            response = self.query_command(':TRAC:POIN:ACT?').strip()
            if response:
                data_points = int(response)
                print(f"Data points available: {data_points}")
                return data_points
            else:
                print("No data points available.")
                return 0
        except Exception as e:
            print(f"Error querying data points: {e}")
            return 0

    def read_data(self, num_readings: int):
        try:
            data = []
            for i in range((num_readings - 1) // 1000 + 1):
                if num_readings - i * 1000 > 1000:
                    data_sel_count = 1000
                else:
                    data_sel_count = num_readings - i * 1000

                raw_data = self.k6.query(f"TRAC:DATA:SEL? {i * 1000 + 1},{data_sel_count}")
                raw_data = raw_data.split(",")
                data.extend(raw_data)
            print(f"Data: {data}")
            return data
        except Exception as e:
            print(f"Error reading data: {e}")
            return None

    def parse_and_execute(self):
        parser = argparse.ArgumentParser(description="Broom vTEST")
        parser.add_argument('--run_pulse_sweep', action='store_true', help='Run pulse sweep')

        args = parser.parse_args()

        try:
            if args.run_pulse_sweep:
                self.run_pulse_sweep()
        except Exception as e:
            print(f'Error parsing arguments: {e}')
            return None

        return args

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
