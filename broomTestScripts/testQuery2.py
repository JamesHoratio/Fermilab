import sys
import os
import csv
import time
import datetime
import pyvisa as visa
import argparse

DEBUG_PRINT_COMMANDS = True
INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"  # Change this to your instrument's resource string
INSTRUMENT_RESOURCE_STRING_2182A = "GPIB0::7::INSTR"  # Change this to your instrument's resource string
SAVED_PARAMETERS_FILENAME = ("sweep_parameters.txt")
class BroomK6221:
    def __init__(self):
        self.K6221Address = INSTRUMENT_RESOURCE_STRING_6221
        self.connected = self.connect6221()
        try:
            
            self.k6.write_termination = '\n'
            self.k6.read_termination = '\n'
            self.k6.timeout = 60000
            self.k6.write('*RST')
            time.sleep(1)
            self.k6.write('SYST:PRES')
            time.sleep(1)
            self.k6.write('SOUR:SWE:ABORT')
            time.sleep(1)
            self.k6.write('SYST:COMM:SER:SEND "*RST"')
            time.sleep(2)
            #self.k6.write('SYST:COMM:SER:SEND "REN"')
            time.sleep(1)
            self.k6.write('SYST:COMM:SER:SEND "ABORT"')
            time.sleep(1)
            #self.k6.write('SYST:COMM:SER:SEND "FORMat:ELEMents READing,TSTamp,RNUMber"')
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
        
    def writeK2182(self, command):
        try:
            self.k6.write(f'SYST:COMM:SER:SEND "{command}"')
        except Exception as e:
            print(f"Error writing to K2182: {e}")

    def queryK2182(self, query: str) -> str:
        try:
            print(f"Querying K2182: {query}")
            self.k6.write(f'SYST:COMM:SER:SEND {query}')
            #time.sleep(0.2)
            response = self.k6.query('SYST:COMM:SER:ENT?')
            print(f"Response from K2182: {response}")
            return response
        except Exception as e:
            print(f"Error querying K2182: {e}")
    
    def testquery(self):
        try:
            self.read_data(1001)
            #time.sleep(3)
            #test = self.k6.query('*IDN?')
            #print(f"Test query: {test}")
        except Exception as e:
            print(f"Error querying test: {e}")

    def get_data_points(self):
        try:
            # Query the number of points in the buffer
            data_points = self.k6.query(':TRAC:POIN:ACT?'.strip())
            print(f"Data points available: '{data_points}'")
            return data_points
        except Exception as e:
            print(f"Error querying data points: {e}")
            return 0

    def read_data(self, num_readings: int):
        """Wait for instruments to finish measuring and read data"""
        # Wait for sweep to finish
        sweep_done = False
        data = []
        try:
            #while not sweep_done:
            #    time.sleep(1)
            #    oper_byte_status = self.k6.query("STAT:OPER:EVEN?")  # Check the event register
            #    oper_byte_status = int(oper_byte_status)  # Convert decimal string to int
            #    sweep_done = oper_byte_status & (1 << 1)  # bit mask to check if sweep done

            # Get the measurements 1000 at a time
            for i in range((num_readings - 1) // 1000 + 1):
                if num_readings - i * 1000 > 1000:  # if more than 1000 readings left
                    data_sel_count = 1000
                else:
                    data_sel_count = num_readings - i * 1000

                # Transfer readings over GPIB
                raw_data = self.k6.query(f"TRAC:DATA:SEL? '{i * 1000}','{data_sel_count}'")
                raw_data = raw_data.split(",")
                data.extend(raw_data)
        except Exception as e:
            print(f"Error reading data: {e}")
            return None
        print (f"Data: {data}")
        return data

    def retestquery(self):
        try:
            #self.testquery('*IDN?')
            #self.k6.write(':SYST:COMM:SER:SEND "*CLS;WAIT500;REN"')
            #time.sleep(1)
            #nanores1 = self.k6.write('SYST:COMM:SER:SEND "PDELta:NVPResent?"')
            #print(f"1: {nanores1}")
            #nanoresponse = self.k6.write('SYST:COMM:SER:ENT?')
            ##print(f"2: {nanoresponse}")
            #self.k6.write('SYST:COMM:SER:SEND "*IDN?"')
            #time.sleep(0.2)
            #response = self.k6.query('SYST:COMM:SER:ENT?')
            #response = self.queryK2182("PDELta:NVPResent?")
            #print(f"Response: {response}")
            #print(f"Response: {self.query_command('SYST:COMM:SER:SEND "*IDN?"')}")
            #self.query_command(":sour:swe:arm:stat?")
            
            reresponse = self.query_command('*IDN?')
            #print(f"Re-response: {reresponse}")
            #print(f"Response: {response}")
        except Exception as e:
            print(f"Error retesting: {e}")

    def testcommand(self, command: str):
        try:
            self.send_command(command)
            print(f"Command sent: {command}")
        except Exception as e:
            print(f"Error sending command: {e}")

    def parse_and_execute(self):
        parser = argparse.ArgumentParser(description="Broom vTEST")
        #parser.add_argument('--testreset', action='store_true', help='Perform a test reset')
        #parser.add_argument('--deviceprimer', action='store_true', help='Prime devices for sweep')
        #parser.add_argument('--armquery', action='store_true', help='Query the arm status')
        #parser.add_argument('--sweep', action='store_true', help='Start the sweep')
        #parser.add_argument('--read', action='store_true', help='Read the data')
        #parser.add_argument('--save', action='store_true', help='Save the data')
        #parser.add_argument('--startsweepcheck', action='store_true', help='Check if the sweep is running')
        #parser.add_argument('--usercheck', action='store_true', help='Check if the user wants to continue')
        #parser.add_argument('--getdatapoints', action='store_true', help='Get the number of data points')
        parser.add_argument('--testquery', action='store_true', help='Query test')
        parser.add_argument('--retestquery', action='store_true', help='Query test test')
        parser.add_argument('--testcommand', action='store_true', help='Send a test command')

        args = parser.parse_args()

        try:
            # Using a dictionary to simulate a switch-case block
            actions = {
                #"testreset": self.testreset,
                #"deviceprimer": self.deviceprimer,
                #"armquery": self.armquery,
                #"sweep": self.sweep_sequence,
                #"read": self.read,
                #"save": self.save_sequence,
                #"startsweepcheck": self.startsweepcheck,
                #"usercheck": self.usercheck,
                #"getdatapoints": self.get_data_points,
                "testquery": self.testquery,
                "retestquery": self.retestquery,
                "testcommand": self.testcommand,
            }

            for action, func in actions.items():
                if getattr(args, action):
                    func()
                    break
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