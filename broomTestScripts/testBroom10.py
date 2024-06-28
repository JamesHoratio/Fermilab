import sys
import csv
import time
import pyvisa as visa
import argparse
import numpy as np
import datetime
import logging

# Constants
DEBUG_PRINT_COMMANDS = True
INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"
TIMEOUT = 60000
SLEEP_INTERVAL = 1

# Setup logging
logging.basicConfig(level=logging.DEBUG if DEBUG_PRINT_COMMANDS else logging.INFO)

class BroomK6221:
    def __init__(self):
        self.K6221Address = INSTRUMENT_RESOURCE_STRING_6221
        self.rm = visa.ResourceManager()
        self.k6 = self.rm.open_resource(self.K6221Address, write_termination='\n', read_termination='\n')
        self.k6.timeout = TIMEOUT
        self.k6.send_end = True
        self.init_instrument()

    def init_instrument(self):
        self.send_command('*RST')
        self.wait_for_completion()
        self.send_command('SOUR:SWE:ABORT')
        self.wait_for_completion()
        self.send_command('SYST:BEEP:STAT OFF')
        self.wait_for_completion()
        self.send_command('FORM:ELEM READ,TST,RNUM,SOUR')
        time.sleep(4)
        self.wait_for_completion()
        self.init_2182A()
        logging.info("Configured Successfully.")

    def init_2182A(self):
        commands = [
            ':INIT:CONT OFF;:ABORT',
            '*CLS',
            ':SYST:PRES',
            '*RST',
            'TRAC:CLE',
            ':SYST:BEEP:STAT OFF',
            ':SYST:REM',
            ":SENS:FUNC 'VOLT:DC'",
            ':SENS:CHAN 1',
            'SYST:COMM:SER:BAUD 19200',
            ':SYST:REM',
            ":SENS:FUNC 'VOLT:DC'",
            ':SENS:CHAN 1',
            ':SENS:VOLT:RANG 0.1',
            ':TRIG:COUN 11',
            ':SENS:VOLT:AZER:STAT ON',
            ':SENS:DEL:TRAN ON',
            ':SYST:ZCH ON',
            ':SYST:ZCH:STAT ON',
            ':SYST:ZCORR:ACQ'
        ]
        for command in commands:
            self.send_command_to_2182A(command)
            self.wait_for_completion_2182A()

    def send_command(self, command):
        logging.debug(f"Sending command: {command}")
        self.k6.write(command)

    def query_command(self, command):
        logging.debug(f'Querying command: {command}')
        return self.k6.query(command)

    def send_command_to_2182A(self, command):
        self.send_command(f'SYST:COMM:SER:SEND "{command}"')

    def flush_buffer(self):
        try:
            self.k6.clear()
        except visa.VisaIOError as e:
            logging.error(f"Error flushing buffer: {e}")

    def wait_for_completion(self):
        self.send_command('*OPC')
        while True:
            response = self.query_command('*OPC?').strip()
            if response == '1':
                break
            time.sleep(SLEEP_INTERVAL)
            logging.debug(f'K6221 OPC response: {response}.')

    def wait_for_completion_2182A(self):
        self.send_command_to_2182A('*OPC')
        while True:
            self.send_command_to_2182A('*OPC?')
            time.sleep(0.05)
            response = self.query_command('SYST:COMM:SER:ENT?').strip()
            if response == '1':
                break
            time.sleep(SLEEP_INTERVAL)
            logging.debug(f'K2182A OPC response: {response}')

    def configure_pulse_sweep(self):
        self.send_command('*RST')
        self.wait_for_completion()
        self.send_command('TRACe:CLEar')
        self.wait_for_completion()
        if self.query_command('SOURce:PDELta:NVPResent?').strip() != '1':
            logging.error("Error establishing connection with the 2182A.")
            return False
        time.sleep(1)
        self.send_command('SYST:BEEP:STAT OFF')
        self.wait_for_completion()

        # Configure the pulse sweep parameters
        self.send_command('SOURce:PDELta:HIGH 0.01')  # High level of pulse (10 mA)
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:LOW 0')  # Low level of pulse (0 mA)
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:COUNt 11')  # Number of pulses
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:WIDth 500e-9')  # Pulse width (500 ns)
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:SDELay 500e-9')  # Off time (500 ns)
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:INTerval 1e-6')  # Total time per cycle (1 us)
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:RANGing BEST')  # Optimal ranging
        self.wait_for_completion()
        self.send_command('SYST:COMM:SER:SEND ":SENS:VOLT:RANG 0.1"')  # Set voltage range on 2182A
        self.wait_for_completion_2182A()
        self.send_command('SOURce:PDELta:SWEep:STATe ON')  # Enable pulse sweep
        self.wait_for_completion()

        # Additional sweep parameters
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
            self.abort_sweep()
            return False
        self.start_sweep()
        return True

    def start_sweep(self):
        self.send_command('INIT:IMM')
        self.send_command_to_2182A('INIT:IMM')
        time.sleep(5)
        self.abort_sweep()

    def abort_sweep(self):
        self.send_command('SOUR:SWE:ABORT')
        self.wait_for_completion()

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
            self.send_command_to_2182A(':DATA?')
            time.sleep(1)
            chunk_data = self.query_command('SYST:COMM:SER:ENT?').split(',')
            if len(chunk_data) > 1:
                data.extend(chunk_data)
                num_readings -= len(chunk_data) // 4
                retries = 0
            else:
                retries += 1
                logging.warning(f"Retry {retries}/10")
        return data

    def write_csv(self, data):
        csv_path = f"Pulse_Sweep_Data_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        with open(csv_path, "w", newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Reading", "Timestamp", "Source Current", "Reading Number"])
            for i in range(0, len(data), 4):
                csv_writer.writerow(data[i:i+4])
        logging.info(f"Data saved to {csv_path}")

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
    logging.info("done")
    logging.info(f"Elapsed Time: {(stop_time - start_time):0.3f}s")
    broom.close()

if __name__ == "__main__":
    main()
    sys.exit(0)
