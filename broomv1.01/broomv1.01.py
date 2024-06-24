import sys
import os
import csv
import time
import datetime
import pyvisa as visa
import argparse

DEBUG_PRINT_COMMANDS = True

INSTRUMENT_RESOURCE_STRING = "GPIB0::12::INSTR"  # Change this to your instrument's resource string
SAVED_PARAMETERS_FILENAME = ("sweep_parameters.txt")

class Broom:
    def __init__(self):
        try:
            self.rm = visa.ResourceManager()
            self.device = self.rm.open_resource(INSTRUMENT_RESOURCE_STRING)
            response = self.device.query('*IDN?')
            print("Instrument ID:", response)
        except visa.VisaIOError as e:
            print(f"Error initializing instrument: {e}")
            sys.exit(1)

    def send_command(self, command: str) -> None:
        try:
            if DEBUG_PRINT_COMMANDS:
                print(f"Sending command: {command}")
            self.device.write(command)
        except visa.VisaIOError as e:
            print(f"Error sending command '{command}': {e}")

    def query_command(self, command: str) -> str:
        try:
            if DEBUG_PRINT_COMMANDS:
                print(f"Querying command: {command}")
            return self.device.query(command)
        except visa.VisaIOError as e:
            print(f"Error querying command '{command}': {e}")
            return ""

    def broomrun(self):
        try:
            self.testreset()
            self.deviceprimer()
            self.armquery()
            self.usercheck()
            self.sweep()
            self.startsweepcheck()
            data = self.read()
            self.save_data(data)
            self.testreset()
        except Exception as e:
            print(f"Error running Broom: {e}")

    def deviceprimer(self):
        try:
            # Abort tests in the other modes
            self.send_command(":SOUR:SWE:ABOR")
            self.send_command(":SOUR:WAVE:ABOR")
            self.send_command("*RST")  # Reset the 6221
            time.sleep(7)  # Wait 7 seconds

            # Query if the 6221 has reset properly
            if self.query_command("*OPC?").strip() != "1":
                print("6221 did not reset properly.")
                sys.exit(1)

            self.send_command(":SYST:COMM:SERIAL:SEND \"*RST\"")  # Reset the 2182A
            time.sleep(5)  # Wait 5 seconds

            # Query if the 2182A has reset properly
            if self.query_command(":SYST:COMM:SERIAL:SEND \"*OPC?\"").strip() != "1":
                print("2182A did not reset properly.")
                sys.exit(1)

            self.send_command("pdel:swe ON")  # Set pulse sweep state
            self.send_command(":form:elem READ,TST,RNUM,SOUR")  # Set readings to be returned
            time.sleep(1)  # Wait 1 second
            self.send_command(":sour:swe:spac LIN")  # Set pulse sweep spacing
            self.send_command(":sour:curr:start 0")  # Set pulse sweep start
            self.send_command(":sour:curr:stop 0.01")  # Set pulse sweep stop
            self.send_command(":sour:curr:poin 11")  # Set pulse count
            self.send_command(":sour:del 0.01")  # Set pulse delay
            self.send_command(":sour:swe:rang BEST")  # Set sweep range
            self.send_command(":sour:pdel:lme 2")  # Set number of low measurements
            self.send_command(":sour:curr:comp 100")  # Set pulse compliance
            self.send_command(":SYST:COMM:SERIAL:SEND \":sens:volt:rang 10\"")  # Set voltage measure range
            self.send_command("UNIT V")  # Set units
            time.sleep(1)
            self.send_command(":sour:swe:arm")  # Arm the pulse sweep
            time.sleep(3)  # Wait 3 seconds
            self.armquery()
        except Exception as e:
            print(f"Error in device primer: {e}")

    def armquery(self):
        try:
            # Query the pulse sweep arm status
            arm_status = self.query_command(":sour:swe:arm:stat?")
            print(f"Pulse sweep armed: {arm_status}")
            return arm_status
        except Exception as e:
            print(f"Error querying arm status: {e}")
            return ""

    def sweep(self):
        try:
            self.send_command(":init:imm")  # Start the pulse sweep
            print("Pulse sweep initiated.")
            time.sleep(4)  # Wait 4 seconds
        except Exception as e:
            print(f"Error initiating sweep: {e}")

    def get_data_points(self):
        try:
            # Query the number of points in the buffer
            data_points = int(self.query_command(":TRAC:POIN:ACT?").strip())
            print(f"Data points available: {data_points}")
            return data_points
        except Exception as e:
            print(f"Error querying data points: {e}")
            return 0

    def read(self):
        try:
            # Read the pulse sweep data
            data_points = self.get_data_points()
            if data_points == 0:
                print("No data points available to read.")
                return ""
            
            data = self.device.query(f":TRAC:DATA? 1,{data_points}")
            print(data)
            return data
        except Exception as e:
            print(f"Error reading data: {e}")
            return ""

    def save_data(self, data):
        try:
            # Save the data to a CSV file
            filename = "pulsesweepdata.csv"
            with open(filename, "w", newline='') as file:
                writer = csv.writer(file)
                # Assuming the data is a single string of comma-separated values
                rows = data.split(',')
                writer.writerow(["Voltage Reading", "Timestamp", "Source Current"])
                for i in range(0, len(rows), 3):
                    if i + 2 < len(rows):
                        writer.writerow([rows[i], rows[i+1], rows[i+2]])
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data: {e}")

    def startsweepcheck(self):
        try:
            # Check if the pulse sweep is running
            sweep_running = self.query_command(":sour:swe:stat?")
            print(f"Pulse sweep running: {sweep_running}")
            return sweep_running
        except Exception as e:
            print(f"Error checking sweep status: {e}")
            return ""

    def usercheck(self):
        # If user decides to abort or continue the Broom
        user_decision = input("Do you want to continue with Broom? (yes/no): ")
        if user_decision.lower() == "no":
            print("Aborting the Broom as per user's request.")
            self.send_command(":SOUR:SWE:ABORT")  # Abort the test
            self.testreset() # Reset the instruments
            sys.exit(1)
        elif user_decision.lower() == "yes":
            print("Resuming Broom.")
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
            self.usercheck()
    
    def testreset(self):
        try:
            self.send_command(":SOUR:SWE:ABOR")
            self.send_command("*RST")
            time.sleep(7)
            
            # Query if the 6221 has reset properly
            if self.query_command("*OPC?").strip() != "1":
                print("6221 did not reset properly.")
                sys.exit(1)

            self.send_command(":SYST:COMM:SERIAL:SEND \"*RST\"")
            time.sleep(5)
            
            # Query if the 2182A has reset properly
            if self.query_command(":SYST:COMM:SERIAL:SEND \"*OPC?\"").strip() != "1":
                print("2182A did not reset properly.")
                sys.exit(1)

            self.query_command(":sour:swe:arm:stat?")
            self.query_command(":sour:swe:stat?")
            print("Test reset successful.")
        except Exception as e:
            print(f"Error in test reset: {e}")

    def close(self):
        try:
            self.device.close()
            self.rm.close()
            print("Connection closed.")
        except Exception as e:
            print(f"Error closing connection: {e}")


    def parse_and_execute(self):
        parser = argparse.ArgumentParser(description="Broom v1.01")
        parser.add_argument('--testreset', action='store_true', help='Perform a test reset')
        parser.add_argument('--deviceprimer', action='store_true', help='Prime devices for sweep')
        parser.add_argument('--armquery', action='store_true', help='Query the arm status')
        parser.add_argument('--sweep', action='store_true', help='Start the sweep')
        parser.add_argument('--read', action='store_true', help='Read the data')
        parser.add_argument('--save', action='store_true', help='Save the data')
        parser.add_argument('--startsweepcheck', action='store_true', help='Check if the sweep is running')
        parser.add_argument('--usercheck', action='store_true', help='Check if the user wants to continue')
        parser.add_argument('--getdatapoints', action='store_true', help='Get the number of data points')

        args = parser.parse_args()

        try:
            # Using a dictionary to simulate a switch-case block
            actions = {
                "testreset": self.testreset,
                "deviceprimer": self.deviceprimer,
                "armquery": self.armquery,
                "sweep": self.sweep_sequence,
                "read": self.read,
                "save": self.save_sequence,
                "startsweepcheck": self.startsweepcheck,
                "usercheck": self.usercheck,
                "getdatapoints": self.get_data_points
            }

            for action, func in actions.items():
                if getattr(args, action):
                    func()
                    break
        except Exception as e:
            print(f"Error parsing arguments: {e}")
            return None

        return args

    def sweep_sequence(self):
        self.usercheck()
        self.sweep()

    def save_sequence(self):
        data = self.read()
        self.save_data(data)


def main():

    broom = Broom()
    args = broom.parse_and_execute()

    if not args:
        try:   
            broom.broomrun()
        finally:
            broom.close()

if __name__ == "__main__":
    main()
