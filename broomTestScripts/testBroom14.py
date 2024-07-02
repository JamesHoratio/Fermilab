import sys
import csv
import time
import argparse
import numpy as np
import datetime
import logging
import pandas as pd
from pymeasure.instruments.keithley import Keithley6221, Keithley2182
from pymeasure.adapters import SerialAdapter
from time import sleep

# Constants
DEBUG_PRINT_COMMANDS = True  # Enable or disable debug printing
TIMEOUT = 60000  # Timeout for VISA operations
SLEEP_INTERVAL = 1  # Interval between retries
GPIB_ADDRESS_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"  # GPIB address for the Keithley 6221
RS232_PORT_2182A = "TCPIP0::169.254.47.133::1394::COM2"  # RS232 port for the Keithley 2182A

# Setup logging
logging.basicConfig(level=logging.DEBUG if DEBUG_PRINT_COMMANDS else logging.INFO)  # Configure logging level

# Set the input parameters for pulse sweep
data_points = 11  # Number of data points
start_current = 0  # Start current in Amps
stop_current = 0.01  # Stop current in Amps
step_current = 0.001  # Step current in Amps
delay = 0.001  # Delay between steps in seconds
pulse_high = 0.01  # Pulse high level in Amps
pulse_low = 0  # Pulse low level in Amps
pulse_count = 11  # Number of pulses
pulse_width = 500e-9  # Pulse width in seconds
pulse_delay = 500e-9  # Pulse delay in seconds
pulse_interval = 1e-6  # Pulse interval in seconds
voltage_range = 0.1  # Voltage range in Volts


class BroomK6221:
    def __init__(self):
        # Initialize the instruments
        self.k6221 = Keithley6221(GPIB_ADDRESS_6221)  # Initialize Keithley 6221 using GPIB
        self.k2182A = Keithley2182(RS232_PORT_2182A)  # Initialize Keithley 2182A using RS232
        self.k6221.reset()
        self.k2182A.reset()
        self.init_instruments()  # Initialize both instruments

    def init_instruments(self):
        try:
            # Configure Keithley 6221
            self.k6221.write('SOUR:SWE:ABOR')  # Abort any ongoing sweep
            self.k6221.write('SYST:BEEP:STAT OFF')  # Disable beep sound
            self.k6221.write('FORM:ELEM READ,TST,RNUM,SOUR')  # Set the format elements for output
            sleep(4)  # Wait for settings to apply

            # Initialize Keithley 2182A
            self.init_2182A()
            logging.info("Configured Successfully.")  # Log successful configuration
        except Exception as e:
            logging.error(f"Initialization failed: {e}")  # Log any initialization errors

    def init_2182A(self):
        # List of commands to initialize the 2182A
        commands = [
            ':INIT:CONT OFF;:ABORT',  # Turn off continuous initiation and abort any ongoing process
            '*CLS',  # Clear status and error queue
            ':SYST:PRES',  # Set system to default settings
            '*RST',  # Reset the instrument
            'TRAC:CLE',  # Clear the trace buffer
            ':SYST:BEEP:STAT OFF',  # Disable beep sound
            ':SYST:REM',  # Set the system to remote mode
            ":SENS:FUNC 'VOLT:DC'",  # Set the measurement function to DC voltage
            ':SENS:CHAN 1',  # Set the measurement channel to 1
            ':SENS:VOLT:RANG 0.1',  # Set the voltage range to 0.1V
            ':TRIG:COUN 11',  # Set the trigger count to 11
            ':SENS:VOLT:AZER:STAT ON',  # Enable auto-zeroing
            ':SENS:DEL:TRAN ON',  # Enable delay on transitions
            ':SYST:ZCH ON',  # Enable zero check
            ':SYST:ZCH:STAT ON',  # Ensure zero check status is on
            ':SYST:ZCORR:ACQ'  # Acquire zero correction
        ]
        for command in commands:
            self.k2182A.write(command)
            self.wait_for_completion_2182A()

    def wait_for_completion(self):
        self.k6221.write('*OPC')  # Send the operation complete command
        while True:
            response = self.k6221.query('*OPC?').strip()  # Query the operation complete status
            if response == '1':  # If operation complete
                break  # Break the loop
            sleep(SLEEP_INTERVAL)  # Sleep for the interval
            logging.debug(f'K6221 OPC response: {response}.')  # Log the response

    def wait_for_completion_2182A(self):
        self.k2182A.write('*OPC')  # Send operation complete command to 2182A
        retries = 0  # Initialize retry count
        while retries < 10:
            self.k2182A.write('*OPC?')  # Query operation complete status from 2182A
            sleep(0.05)  # Sleep for a short interval
            response = self.k2182A.read().strip()  # Read the response from 2182A
            if response == '1':  # If operation complete
                break  # Break the loop
            sleep(SLEEP_INTERVAL)  # Sleep for the interval
            retries += 1  # Increment retry count
            logging.debug(f'K2182A OPC response: {response}')  # Log the response
        if retries == 10:  # If retries exhausted
            logging.error("Failed to get OPC response from 2182A")  # Log the error

    def configure_pulse_sweep(self):
        try:
            # Reset the instrument
            self.k6221.write('*RST')  # Reset the instrument
            self.wait_for_completion()  # Wait for completion
            self.k6221.write('TRACe:CLEar')  # Clear the trace
            self.wait_for_completion()  # Wait for completion

            # Configure the pulse sweep parameters
            self.k6221.write(f'SOURce:PDELta:HIGH {pulse_high}')  # Set high level of pulse (10 mA)
            self.wait_for_completion()  # Wait for completion
            self.k6221.write(f'SOURce:PDELta:LOW {pulse_low}')  # Set low level of pulse (0 mA)
            self.wait_for_completion()  # Wait for completion
            self.k6221.write(f'SOURce:PDELta:COUNt {pulse_count}')  # Set number of pulses
            self.wait_for_completion()  # Wait for completion
            self.k6221.write(f'SOURce:PDELta:WIDth {pulse_width}')  # Set pulse width (500 ns)
            self.wait_for_completion()  # Wait for completion
            self.k6221.write(f'SOURce:PDELta:SDELay {pulse_delay}')  # Set off time (500 ns)
            self.wait_for_completion()  # Wait for completion
            self.k6221.write(f'SOURce:PDELta:INTerval {pulse_interval}')  # Set total time per cycle (1 us)
            self.wait_for_completion()  # Wait for completion
            self.k6221.write('SOURce:PDELta:RANGing BEST')  # Set optimal ranging
            self.wait_for_completion()  # Wait for completion
            self.k2182A.write(":SENS:VOLT:RANG 0.1")  # Set voltage range on 2182A
            self.wait_for_completion_2182A()  # Wait for completion on 2182A
            self.k6221.write('SOURce:PDELta:SWEep:STATe ON')  # Enable pulse sweep
            self.wait_for_completion()  # Wait for completion

            # Additional sweep parameters
            self.k6221.write('SOURce:SWEep:SPACing LIN')  # Set sweep spacing to linear
            self.wait_for_completion()  # Wait for completion
            self.k6221.write('SOURce:CURRent:STARt 0')  # Set start current to 0
            self.wait_for_completion()  # Wait for completion
            self.k6221.write(f'SOURce:CURRent:STOP {stop_current}')  # Set stop current to 10 mA
            self.wait_for_completion()  # Wait for completion
            self.k6221.write(f'SOURce:CURRent:STEP {step_current}')  # Set current step to 1 mA
            self.wait_for_completion()  # Wait for completion
            self.k6221.write('SOURce:DEL 0.001')  # Set delay
            self.wait_for_completion()  # Wait for completion
            self.k6221.write('SOUR:SWE:RANG BEST')  # Set optimal ranging
            self.wait_for_completion()  # Wait for completion
            self.k6221.write('SYST:COMM:SER:SEND "trig:coun 1"')  # Configure trigger and source
            self.wait_for_completion_2182A()  # Wait for completion
            self.k6221.write('SYST:COMM:SER:SEND "Sour:trig ext"')
            self.wait_for_completion_2182A()  # Wait for completion
            self.k6221.write('SYST:COMM:SER:SEND "trig:sour ext"')

            return True  # Return True if configuration is successful
        except Exception as e:
            logging.error(f"Failed to configure pulse sweep: {e}")
            return False  # Return False if configuration fails

    def run_pulse_sweep(self):
        if not self.configure_pulse_sweep():  # If configuration fails
            return  # Exit the function
        if not self.user_check():  # If user does not want to continue
            return  # Exit the function

        self.flush_buffer()  # Flush the buffer
        self.k6221.write('INITiate:IMMediate')  # Start the pulse sweep
        sleep(5)  # Sleep for 5 seconds to allow sweep to complete
        self.k6221.write('SOUR:SWE:ABOR')  # Abort the sweep
        sleep(1)  # Sleep for 1 second

        data = self.k6221.query('TRAC:DATA?').split(',')  # Query the data and split it
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
        self.k6221.shutdown()  # Close the Keithley 6221
        self.k2182A.shutdown()  # Close the Keithley 2182A

def main():
    start_time = time.time()  # Record start time
    broom = BroomK6221()  # Create an instance of BroomK6221
    broom.parse_and_execute()  # Parse arguments and execute based on them
    stop_time = time.time()  # Record stop time
    logging.info("done")  # Log completion
    logging.info(f"Elapsed Time: {(stop_time - start_time):0.3f}s")  # Log elapsed time
    broom.close()  # Close the instruments

if __name__ == "__main__":
    main()  # Execute main function
    sys.exit(0)  # Exit the script
