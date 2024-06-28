import sys
import csv
import time
import pyvisa as visa
import argparse
import numpy as np
import datetime
import logging

# Constants
DEBUG_PRINT_COMMANDS = True  # Enable or disable debug printing
INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"  # Resource string for the instrument
TIMEOUT = 60000  # Timeout for VISA operations
SLEEP_INTERVAL = 1  # Interval between retries

# Setup logging
logging.basicConfig(level=logging.DEBUG if DEBUG_PRINT_COMMANDS else logging.INFO)  # Configure logging level

class BroomK6221:
    def __init__(self):
        self.K6221Address = INSTRUMENT_RESOURCE_STRING_6221  # Set the instrument address
        self.rm = visa.ResourceManager()  # Create a resource manager
        self.k6 = self.rm.open_resource(self.K6221Address, write_termination='\n', read_termination='\n')  # Open the resource
        self.k6.timeout = TIMEOUT  # Set timeout for the instrument
        self.k6.send_end = True  # Enable send end
        self.init_instrument()  # Initialize the instrument

    def init_instrument(self):
        self.send_command('*RST')  # Reset the instrument
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOUR:SWE:ABORT')  # Abort any ongoing sweep
        self.wait_for_completion()  # Wait for completion
        self.send_command('SYST:BEEP:STAT OFF')  # Disable beep
        self.wait_for_completion()  # Wait for completion
        self.send_command('FORM:ELEM READ,TST,RNUM,SOUR')  # Set the format elements
        time.sleep(4)  # Sleep for 4 seconds
        self.wait_for_completion()  # Wait for completion
        self.init_2182A()  # Initialize 2182A instrument
        logging.info("Configured Successfully.")  # Log successful configuration

    def init_2182A(self):
        commands = [  # List of commands to initialize 2182A
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
            self.send_command_to_2182A(command)  # Send command to 2182A
            self.wait_for_completion_2182A()  # Wait for command completion

    def send_command(self, command):
        logging.debug(f"Sending command: {command}")  # Log the command being sent
        self.k6.write(command)  # Write the command to the instrument

    def query_command(self, command):
        logging.debug(f'Querying command: {command}')  # Log the command being queried
        return self.k6.query(command)  # Query the command from the instrument

    def send_command_to_2182A(self, command):
        logging.debug(f'Sending command: {command} to 2182A')
        self.send_command(f'SYST:COMM:SER:SEND "{command}"')  # Send a command to 2182A

    def query_command_to_2182A(self, command):
        logging.debug(f'Querying command: {command} to 2182A')
        self.send_command_to_2182A(command)
        return self.query_command('SYST:COMM:SER:ENT?').strip()

    def flush_buffer(self):
        try:
            self.k6.clear()  # Clear the instrument buffer
        except visa.VisaIOError as e:
            logging.error(f"Error flushing buffer: {e}")  # Log any error in flushing buffer

    def wait_for_completion(self):
        self.send_command('*OPC')  # Send the operation complete command
        while True:
            response = self.query_command('*OPC?').strip()  # Query the operation complete status
            if response == '1':  # If operation complete
                break  # Break the loop
            time.sleep(SLEEP_INTERVAL)  # Sleep for the interval
            logging.debug(f'K6221 OPC response: {response}.')  # Log the response

    def wait_for_completion_2182A(self):
        self.send_command_to_2182A('*OPC')  # Send operation complete command to 2182A
        retries = 0  # Initialize retry count
        while retries < 10:
            self.send_command_to_2182A('*OPC?')  # Query operation complete status from 2182A
            time.sleep(0.05)  # Sleep for a short interval
            response = self.query_command('SYST:COMM:SER:ENT?').strip()  # Query the response from 2182A
            if response == '1':  # If operation complete
                break  # Break the loop
            time.sleep(SLEEP_INTERVAL)  # Sleep for the interval
            retries += 1  # Increment retry count
            logging.debug(f'K2182A OPC response: {response}')  # Log the response
        if retries == 10:  # If retries exhausted
            logging.error("Failed to get OPC response from 2182A")  # Log the error

    def configure_pulse_sweep(self):
        self.send_command('*RST')  # Reset the instrument
        self.wait_for_completion()  # Wait for completion
        self.send_command('TRACe:CLEar')  # Clear the trace
        self.wait_for_completion()  # Wait for completion
        # Check and disable delta mode on 2182A
        delta_mode = self.query_command_2182A(':SOURce:PDELta:NVPResent?')
        if delta_mode == '1':
            self.send_command_to_2182A(':SOURce:PDELta:STATe OFF')
            self.wait_for_completion_2182A()
        time.sleep(1)  # Sleep for 1 second
        self.send_command('SYST:BEEP:STAT OFF')  # Disable beep
        self.wait_for_completion()  # Wait for completion

        # Configure the pulse sweep parameters
        self.send_command('SOURce:PDELta:HIGH 0.01')  # Set high level of pulse (10 mA)
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOURce:PDELta:LOW 0')  # Set low level of pulse (0 mA)
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOURce:PDELta:COUNt 11')  # Set number of pulses
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOURce:PDELta:WIDth 500e-9')  # Set pulse width (500 ns)
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOURce:PDELta:SDELay 500e-9')  # Set off time (500 ns)
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOURce:PDELta:INTerval 1e-6')  # Set total time per cycle (1 us)
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOURce:PDELta:RANGing BEST')  # Set optimal ranging
        self.wait_for_completion()  # Wait for completion
        self.send_command('SYST:COMM:SER:SEND ":SENS:VOLT:RANG 0.1"')  # Set voltage range on 2182A
        self.wait_for_completion_2182A()  # Wait for completion on 2182A
        self.send_command('SOURce:PDELta:SWEep:STATe ON')  # Enable pulse sweep
        self.wait_for_completion()  # Wait for completion

        # Additional sweep parameters
        self.send_command('SOURce:SWEep:SPACing LIN')  # Set sweep spacing to linear
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOURce:CURRent:STARt 0')  # Set start current to 0
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOURce:CURRent:STOP 0.01')  # Set stop current to 10 mA
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOURce:CURRent:STEP 0.001')  # Set current step to 1 mA
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOURce:DEL 0.001')  # Set delay
        self.wait_for_completion()  # Wait for completion
        self.send_command('SOUR:SWE:RANG BEST')  # Set optimal ranging
        self.wait_for_completion()  # Wait for completion
        self.send_command('SYST:COMM:SER:SEND ":trig:coun 1;:sour ext"')  # Configure trigger and source
        self.wait_for_completion()  # Wait for completion

        return True  # Return True if configuration is successful

    def run_pulse_sweep(self):
        if not self.configure_pulse_sweep():  # If configuration fails
            return  # Exit the function
        if not self.user_check():  # If user does not want to continue
            return  # Exit the function

        self.flush_buffer()  # Flush the buffer
        self.send_command('INITiate:IMMediate')  # Start the pulse sweep
        time.sleep(5)  # Sleep for 5 seconds
        self.send_command('SOUR:SWE:ABOR')  # Abort the sweep
        time.sleep(1)  # Sleep for 1 second

        data = self.k6.query('TRAC:DATA?').split(',')  # Query the data and split it
        self.save_data(data)  # Save the data

    def save_data(self, data):
        csv_path = f'BroomData_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'  # Create CSV file path
        with open(csv_path, mode='w', newline='') as csv_file:  # Open CSV file in write mode
            csv_writer = csv.writer(csv_file)  # Create a CSV writer
            csv_writer.writerow(["Reading", "Timestamp", "Source Current", "Reading Number"])  # Write header row
            for i in range(0, len(data), 4):  # Iterate over the data in chunks of 4
                csv_writer.writerow(data[i:i+4])  # Write each chunk to the CSV file
        logging.info(f"Data saved to {csv_path}")  # Log the path of the saved data

    def user_check(self):
        user_response = input("Do you want to continue with the pulse sweep? (yes/no): ").strip().lower()  # Get user input
        return user_response == 'yes'  # Return True if user input is 'yes'

    def parse_and_execute(self):
        parser = argparse.ArgumentParser(description="Broom vTEST")  # Create argument parser
        parser.add_argument('--run_pulse_sweep', action='store_true', help='Run pulse sweep')  # Add argument for running pulse sweep
        args = parser.parse_args()  # Parse the arguments
        if args.run_pulse_sweep:  # If run_pulse_sweep argument is passed
            self.run_pulse_sweep()  # Run the pulse sweep

    def close(self):
        self.k6.close()  # Close the instrument resource
        self.rm.close()  # Close the resource manager

def main():
    start_time = time.time()  # Record start time
    broom = BroomK6221()  # Create an instance of BroomK6221
    broom.parse_and_execute()  # Parse arguments and execute based on them
    stop_time = time.time()  # Record stop time
    logging.info("done")  # Log completion
    logging.info(f"Elapsed Time: {(stop_time - start_time):0.3f}s")  # Log elapsed time
    broom.close()  # Close the instrument and resource manager

if __name__ == "__main__":
    main()  # Execute main function
    sys.exit(0)  # Exit the script
