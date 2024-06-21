import sys
import os
import csv
import struct
import time
import datetime
import textwrap
import pyvisa as visa
from instrcomms import Communications
from instrgui import InstrumentOption, open_gui_return_input
import PulseIVSweepQADv2 as sweep

DEBUG_PRINT_COMMANDS = True

INSTRUMENT_RESOURCE_STRING = "GPIB0::12::INSTR"  # Change this to your instrument's resource string

SAVED_PARAMETERS_FILENAME = ("sweep_parameters.txt")

# Define the sweep parameters

class PulseSweepProgram:
    def __init__(self):
        self.rm = visa.ResourceManager()
        self.device = self.rm.open_resource(INSTRUMENT_RESOURCE_STRING)
        response = self.device.query('*IDN?')
        print("Instrument ID:", response)
        #self.comms = Communications(self.device)

    def send_command(self, command: str) -> None:
        print(f"Sending command: {command}")
        self.device.write(command)

    def query_command(self, command: str) -> str:
        print(f"Querying command: {command}")
        return self.device.query(command)

    def deviceprimer(self):
        # Abort tests in the other modes
        self.send_command(":SOUR:SWE:ABOR")
        self.send_command(":SOUR:WAVE:ABOR")
        self.send_command("*RST")  # Reset the 6221
        time.sleep(2) # Wait 2 seconds
        self.send_command(":SYST:COMM:SERIAL:SEND \"*RST\"")  # Reset the 2182A
        time.sleep(3) # Wait 3 seconds
        #self.send_command(":SYST:COMM:SERIAL:SEND \":SYST:RSEN ON\"")
        time.sleep(1) # Wait 1 second
        self.send_command("pdel:swe ON")  # Set pulse sweep state
        self.send_command(":form:elem READ,TST,RNUM,SOUR")  # Set readings to be returned
        #self.send_command(":SOUR:CURR:COMP {volt_compliance}")  # Set voltage compliance
        self.send_command(":sour:swe:spac LIN")  # Set pulse sweep spacing
        self.send_command(":sour:curr:start 0")  # Set pulse sweep start
        self.send_command(":sour:curr:stop 0.01")  # Set pulse sweep stop
        self.send_command(":sour:curr:poin 11")  # Set pulse count
        self.send_command(":sour:del 0.01")  # Set pulse delay
        self.send_command(":sour:swe:rang BEST")  # Set sweep range # Best uses lowest range which will handle all sweep steps
        self.send_command(":sour:pdel:lme 2")  # Set number of low measurements
        self.send_command(":sour:curr:comp 100")  # Set pulse compliance
        #self.send_command(f"sour:curr:step {pulsesweepstep}")  # Set pulse sweep step
        self.send_command(":SYST:COMM:SERIAL:SEND \":sens:volt:rang 10\"")  # Set voltage measure range
        #self.send_command(f"sens:aver:wind 0")  # Set averaging window
        self.send_command("UNIT V")  # Set units (other options are OHMS, W, SIEM)
        time.sleep(1)
        self.send_command(":sour:swe:arm")  # Arm the pulse sweep
        time.sleep(3) # Wait 3 seconds

    def sweep(self):
        self.send_command(":init:imm") # Start the pulse sweep
        time.sleep(4) # Wait 4 seconds

    def read(self):
        # Read the pulse sweep data
        data = self.query_command(":trac:data:read?")
        print(data)
        return data

def get_user_input(prompt: str, valid_options=None):
        while True:
            value = input(prompt).strip()
            if not valid_options or value in valid_options:
                return value
            print(f"Invalid input. Valid options are: {', '.join(valid_options)}")
    
def read_data():
    """Wait for instruments to finish measuring and read data"""
    # Wait for sweep to finish
    num_readings = 65534  # Number of readings to read
    sweep_done = False
    data = []
    while not sweep_done:
        time.sleep(1)
        oper_byte_status = PulseSweepProgram.send_command(":STAT:OPER:EVEN?")  # Check the event register
        oper_byte_status = int(oper_byte_status)  # Convert decimal string to int
        sweep_done = oper_byte_status & (1 << 1)  # bit mask to check if sweep done

    # Get the measurements 1000 at a time
    for i in range((64 - 1) // 1000 + 1):
        if num_readings - i * 1000 > 1000:  # if more than 1000 readings left
            data_sel_count = 1000
        else:
            data_sel_count = num_readings - i * 1000

        # Transfer readings over GPIB
        raw_data = PulseSweepProgram.send_command(f":TRAC:DATA:SEL? {i * 1000},{data_sel_count}")
        raw_data = raw_data.split(",")
        data.extend(raw_data)

    return data


def instrument_config(ip_string: str = None):
    if ip_string is None:
        connection_type = get_user_input("Enter connection type (IP/USB): ", ["IP", "USB"]).upper()
        ip_address = input("Enter IP address: ").strip()
    if connection_type == "IP":
        ip_string = f"TCPIP::{ip_address}::INSTR"
    elif connection_type == "USB":
        ip_string = f"USB::{ip_address}::INSTR"
    else:
        print("Invalid connection type.")
        return
        
def main():
    program = PulseSweepProgram()
    program.deviceprimer()
    program.sweep()
    data = read_data()
    print(data)
    #data = read_data(program, 11)
    #data = [PulseSweepProgram.read()]


if __name__ == "__main__":
    main() 