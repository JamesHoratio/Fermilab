import sys
import os
import csv
import time
import datetime
import pyvisa as visa
import argparse

DEBUG_PRINT_COMMANDS = True

INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"  # Change this to your 6221's resource string
INSTRUMENT_RESOURCE_STRING_2182A = "GPIB0::7::INSTR"  # Change this to your 2182A's resource string
SAVED_PARAMETERS_FILENAME = ("sweep_parameters.txt")

class BroomCurrentSource:
    def __init__(self, device):
        self.device = device
class Broom:
    def __init__(self):
        try:
            self.rm = visa.ResourceManager()
            self.list_resources()
            self.device_6221 = self.connect_instrument(INSTRUMENT_RESOURCE_STRING_6221)
            self.device_2182A = self.connect_instrument(INSTRUMENT_RESOURCE_STRING_2182A)
            response_6221 = self.device_6221.query('*IDN?')
            response_2182A = self.device_2182A.query('*IDN?')
            print("6221 ID:", response_6221)
            print("2182A ID:", response_2182A)
        except visa.VisaIOError as e:
            print(f"Error initializing instruments: {e}")
            sys.exit(1)

    def connect_instrument(self, resource_string):
        try:
            instrument = self.rm.open_resource(resource_string)
            instrument.timeout = 10000  # Set timeout to 10 seconds
            return instrument
        except visa.VisaIOError as e:
            print(f"Error connecting to instrument {resource_string}: {e}")
            sys.exit(1)

    def list_resources(self):
        try:
            resources = self.rm.list_resources()
            print("Available VISA resources:")
            for resource in resources:
                print(resource)
        except Exception as e:
            print(f"Error listing VISA resources: {e}")

    def send_command(self, device, command: str) -> None:
        try:
            if DEBUG_PRINT_COMMANDS:
                print(f"Sending command to {device}: {command}")
            device.write(command)
        except visa.VisaIOError as e:
            print(f"Error sending command '{command}' to {device}: {e}")

    def query_command(self, device, command: str) -> str:
        try:
            if DEBUG_PRINT_COMMANDS:
                print(f"Querying command from {device}: {command}")
            return device.query(command)
        except visa.VisaIOError as e:
            print(f"Error querying command '{command}' from {device}: {e}")
            return ""

    def ping_device(self, device_name):
        try:
            if device_name == "6221":
                device = self.device_6221
                response = self.query_command(device, '*IDN?')
                if response:
                    print(f"6221 is responding: {response}")
                else:
                    print("6221 is not responding.")
            elif device_name == "2182A":
                device = self.device_2182A
                response = self.query_command(device, '*IDN?')
                if response:
                    print(f"2182A is responding: {response}")
                else:
                    print("2182A is not responding.")
            else:
                print(f"Unknown device: {device_name}")
        except Exception as e:
            print(f"Error pinging device {device_name}: {e}")

    def broomrun(self):
        try:
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
            self.send_command(self.device_6221, ":SOUR:SWE:ABOR")
            self.send_command(self.device_6221, ":SOUR:WAVE:ABOR")
            self.send_command(self.device_6221, "*RST")  # Reset the 6221
            time.sleep(7)  # Wait 7 seconds

            # Query if the 6221 has reset properly
            if self.query_command(self.device_6221, "*OPC?").strip() != "1":
                print("6221 did not reset properly.")
                sys.exit(1)

            self.send_command(self.device_2182A, "*RST")  # Reset the 2182A
            time.sleep(5)  # Wait 5 seconds

            # Query if the 2182A has reset properly
            if self.query_command(self.device_2182A, "*OPC?").strip() != "1":
                print("2182A did not reset properly.")
                sys.exit(1)

            self.send_command(self.device_6221, "pdel:swe ON")  # Set pulse sweep state
            self.send_command(self.device_6221, ":form:elem READ,TST,RNUM,SOUR")  # Set readings to be returned
            time.sleep(1)  # Wait 1 second
            self.send_command(self.device_6221, ":sour:swe:spac LIN")  # Set pulse sweep spacing
            self.send_command(self.device_6221, ":sour:curr:start 0")  # Set pulse sweep start
            self.send_command(self.device_6221, ":sour:curr:stop 0.01")  # Set pulse sweep stop
            self.send_command(self.device_6221, ":sour:curr:poin 11")  # Set pulse count
            self.send_command(self.device_6221, ":sour:del 0.01")  # Set pulse delay
            self.send_command(self.device_6221, ":sour:swe:rang BEST")  # Set sweep range
            self.send_command(self.device_6221, ":sour:pdel:lme 2")  # Set number of low measurements
            self.send_command(self.device_6221, ":sour:curr:comp 100")  # Set pulse compliance
            self.send_command(self.device_2182A, ":sens:volt:rang 10")  # Set voltage measure range
            self.send_command(self.device_6221, "UNIT V")  # Set units
            time.sleep(1)
            self.send_command(self.device_6221, ":sour:swe:arm")  # Arm the pulse sweep
            time.sleep(3)  # Wait 3 seconds
            self.armquery()
        except Exception as e:
            print(f"Error in device primer: {e}")

    def armquery(self):
        try:
            # Query the pulse sweep arm status
            arm_status = self.query_command(self.device_6221, ":sour:swe:arm:stat?")
            print(f"Pulse sweep armed: {arm_status}")
            return arm_status
        except Exception as e:
            print(f"Error querying arm status: {e}")
            return ""

    def sweep(self):
        try:
            self.send_command(self.device_6221, ":init:imm")  # Start the pulse sweep
            print("Pulse sweep initiated.")
            time.sleep(4)  # Wait 4 seconds
        except Exception as e:
            print(f"Error initiating sweep: {e}")

    def get_data_points(self):
        try:
            # Query the number of points in the buffer
            data_points = int(self.query_command(self.device_6221, ":TRAC:POIN:ACT?").strip())
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
            
            data = self.query_command(self.device_6221, f":TRAC:DATA? 1,{data_points}")
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
            sweep_running = self.query_command(self.device_6221, ":sour:swe:stat?")
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
            self.send_command(self.device_6221, ":SOUR:SWE:ABORT")  # Abort the test
            self.testreset()  # Reset the instruments
            sys.exit(1)
        elif user_decision.lower() == "yes":
            print("Resuming Broom.")
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
            self.usercheck()
    
    def testreset(self):
        try:
            self.send_command(self.device_6221, ":SOUR:SWE:ABOR")
            self.send_command(self.device_6221, "*RST")
            time.sleep(3)
            
            # Query if the 6221 has reset properly
            if self.query_command(self.device_6221, "*OPC?").strip() != "1":
                print("6221 did not reset properly.")
                sys.exit(1)

            self.send_command(self.device_2182A, "*RST")
            time.sleep(3)
            
            if self.query_command(self.device_2182A, "*OPC?").strip() != "1":
                print("2182A did not reset properly.")
                sys.exit(1)

            self.query_command(self.device_6221, ":sour:swe:arm:stat?")
            self.query_command(self.device_6221, ":sour:swe:stat?")
            print("Test reset successful.")
        except Exception as e:
            print(f"Error in test reset: {e}")

    def close(self):
        try:
            self.device_6221.close()
            self.device_2182A.close()
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
        parser.add_argument('--ping', nargs='?', const='all', help='Ping devices to check if they are responding')

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
                "getdatapoints": self.get_data_points,
            }

            if args.ping:
                if args.ping == 'all':
                    self.ping_device("6221")
                    self.ping_device("2182A")
                else:
                    self.ping_device(args.ping)
            else:
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
