import sys
import csv
import time
import pyvisa as visa
import argparse
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
import math
import datetime
import textwrap



date = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
csv_path = f".\\Pulse_Sweep_Data{date}.csv"


DEBUG_PRINT_COMMANDS = True
INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"
INSTRUMENT_RESOURCE_STRING_2182A = "GPIB0::7::INSTR"
DATA_FILENAME = "pulse_sweep_data.csv"
error_messages = []
data = []
raw_reading = []
class BroomK6221:
    def __init__(self):
        self.K6221Address = INSTRUMENT_RESOURCE_STRING_6221
        self.rm = visa.ResourceManager()
        self.k6 = self.rm.open_resource(self.K6221Address, write_termination='\n', read_termination='\n')
        self.k6.timeout = 60000
        self.k6.send_end = True
        self.init_instrument()
    
    def init_instrument(self):
        self.send_command('*RST') # Reset instrument
        self.wait_for_completion()
        self.send_command('SOUR:SWE:ABORT') # Abort any ongoing sweeps
        self.wait_for_completion()
        self.send_command('SYST:BEEP:STAT OFF') # Turn off beeper
        self.wait_for_completion()
        self.send_command('FORM:ELEM READ,TST,RNUM,SOUR;') # Set format to read, timestamp, reading number, source
        time.sleep(4)
        self.wait_for_completion()
        self.send_command('SYST:COMM:SER:SEND ":INIT:CONT OFF;:ABORT"') # Abort any ongoing measurements
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND "*CLS"') # Clear Model 2182
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND ":SYST:PRES"') # Preset Model 2182
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND "*RST"') # Clear registers
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND "TRAC:CLE"') # Clear readings from buffer
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND ":SYST:BEEP:STAT OFF"') # Turn off beeper
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND ":SYST:REM"') # Set remote mode
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND ":SENS:FUNC \'VOLT:DC\'"') # Set function to DC voltage
        self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:SEND ":SENS:CHAN 1"') # Set channel to 1
        self.wait_for_completion_2182A()
        #self.send_command('SYST:COMM:SER:SEND ":FORUM:ELEM READ"') # Set format to read
        #self.wait_for_completion_2182A()
        #self.send_command('SYST:COMM:SER:SEND ":TRIG:SOUR IMM"') # Set trigger source to immediate
        #self.wait_for_completion_2182A()
        self.send_command('SYST:COMM:SER:BAUD 19200') # Set baud rate to 19200
        self.wait_for_completion_2182A()
        
        
        #errormessages = ''
        #errormessages = self.query_command('SYSTem:ERRor?')
        #error_messages.append(errormessages)
        #time.sleep(2)
        #self.send_command('SYST:COMM:SER:SEND "SYST:ERR?"') # Query 2182A for errors
        #time.sleep(0.05)
        ##K2182A_error_messages = ''
        #K2182A_error_messages = self.query_command('SYST:COMM:SER:ENT?') # Query response
        #error_messages.append(K2182A_error_messages)
        #time.sleep(2)
        #if not error_messages:
        #    print("No error messages.")
        #else:
        #    for i, message in enumerate(error_messages, 1):
        #        print(f"Error {i}: {message}")
        #self.wait_for_completion()
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
            time.sleep(2)
            if DEBUG_PRINT_COMMANDS:
                print(f'K6221 OPC response: {response}.')
        

    def wait_for_completion_2182A(self):
        self.send_command('SYST:COMM:SER:SEND "*OPC"') # Send OPC command to 2182A
        response = ''
        while response.strip() != '1':
            self.send_command('SYST:COMM:SER:SEND "*OPC?"') # Query OPC status
            time.sleep(0.05)
            response = self.query_command('SYST:COMM:SER:ENT?') # Query response
            if DEBUG_PRINT_COMMANDS:
                print(f'K2182A OPC response: {response}')
            time.sleep(2)

    def configure_pulse_sweep(self):
        self.send_command('*RST') # Reset instrument
        self.wait_for_completion()
        self.send_command('SOURce:CLEar') # Clear source settings
        self.wait_for_completion()
        self.send_command('TRACe:CLEar') # Clear readings from buffer
        self.wait_for_completion()
        #self.send_command('TRACe:POINts 65536') # Specify buffer size (number of readings to store): 1 to 65536.
        #self.wait_for_completion()
        self.query_command('SOURce:PDELta:NVPResent?') # Query connection to 2182A: 1 = yes, 0 = no
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:HIGH 0.01') # Set high pulse value (amps) currently set to 10mA: possible range = [-105e-3, 105e-3]. Default = 1e3
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:LOW 0') # Set low pulse value (amps) currently set to 0mA: possible range = [-105e-3, 105e-3]. Default = 0
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:COUNt 11') # Set number of Pulse Delta readings to perform: 1 to 65636 or INFinity. Default = INF
        self.wait_for_completion()
        #self.send_command('SOURce:PDELta:LMEeasure 2') # Set number of low measurement per cycle: 1 or 2. Default = 2
        #self.wait_for_completion()
        self.send_command('SOURce:PDELta:WIDth 0.0001') # Set pulse width (seconds) Set at 100µs: 50e-6 to 12e-3. Default = 110e-6
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:SDELay 6e-5') # Set source delay (seconds) Set at 60µs pulse delay: 16e-6 to 11.966e-3. Default = 16e-6
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:INTerval 5') # Set interval (in PLCs (Power Line Cycles (Interval of 0.1s @ 60Hz power))) for each pulse cycle: 5 to 999999. Default = 5
        self.wait_for_completion()
        self.send_command('SOURce:PDELta:RANGing BEST') # Select fixed pulse source range: BEST or FIXed. DEfault = BEST
        self.wait_for_completion()
        self.send_command('SYST:COMM:SER:SEND ":SENS:VOLT:RANG 0.1"') # Set 2182A voltage range to 100mV
        self.wait_for_completion_2182A()
        self.send_command('SOURce:PDELta:SWEep:STATe ON') # Enable or disable Sweep output mode. Default = OFF
        self.wait_for_completion()
        self.send_command('SOURce:SWEep:SPACing LIN') # Select linear or logarithmic spacing for sweep points.
        self.wait_for_completion()
        self.send_command('SOURce:CURRent:STARt 0') # Start at 0mA
        self.wait_for_completion()
        self.send_command('SOURce:CURRent:STOP 0.01') # Stop at 10mA
        self.wait_for_completion()
        self.send_command('SOURce:CURRent:STEP 0.001') # Step by 1mA or self.send_command('SOUR:CURR:POIN 11') # Set number of points in sweep: 11
        self.wait_for_completion()
        self.send_command('SOURce:DEL 0.001') # Set source delay (seconds) Set at 6ms: 1e-3 to 999999.999. Default = 1
        self.wait_for_completion()
        self.send_command('SOUR:SWE:RANG BEST') # BEST uses lowest range which will handle all sweep values.
        self.wait_for_completion()



        #self.send_command('SOURce:RANGe:AUTO ON')
        #self.wait_for_completion()

        self.send_command('SOUR:PDEL:ARM') # Arm the Pulse Delta measurement
        
        if not self.user_check():
            self.send_command(':SOUR:SWE:ABORT') # Abort sweep
            self.wait_for_completion()
            return False
        self.send_command('INIT:IMM') # Start sweep

        time.sleep(5)
        self.send_command(':SOUR:SWE:ABORT') # Abort sweep
        self.wait_for_completion()

        time.sleep(1)
        return True

    def run_pulse_sweep(self):
        if self.configure_pulse_sweep():
            data_points = 44
            if data_points > 0:
                data = self.read_data(data_points)
                self.write_csv(data)
    #def get_data_points(self):
    #    response = self.query_command(':TRAC:POIN:ACT?').strip()
    #    return int(response) if response else 0 # Return 0 if no response
    def read_data(self, num_readings: int):
        """Wait for instruments to finish measuring and read data"""
        # Wait for sweep to finish
        sweep_done = False
        data = []
        #while not sweep_done:
        #    time.sleep(1)
        #    oper_byte_status = self.k6.query(
        #        "STAT:OPER:EVEN?"
        #    )  # Check the event register
        #    oper_byte_status = int(oper_byte_status)  # Convert decimal string to int
        #    sweep_done = oper_byte_status & (1 << 1)  # bit mask to check if sweep done

        # Get the measurements 1000 at a time
        for i in range((num_readings - 1) // 1000 + 1):
            if num_readings - i * 1000 > 1000:  # if more than 1000 readings left
                data_sel_count = 1000
            else:
                data_sel_count = num_readings - i * 16

            # Transfer readings over GPIB
            raw_data = self.k6.query(f"TRAC:DATA:SEL? {i * 16},{data_sel_count}")
            raw_data = raw_data.split(",")
            data.extend(raw_data)

        return data
    def write_csv(data, csv_path: str):
        """Write data to csv file"""
        # Create and open file
        with open(csv_path, "a+", encoding="utf-8") as csv_file:
            # Write the measurements to the CSV file
            csv_file.write("Reading, Timestamp, Source Current, Reading Number\n")

            # We queried 4 values per reading, so iterate over groups of 4 elements
            for i in range(0, len(data), 4):
                v_reading = data[i]
                time_stamp = data[i + 1]
                source_current = data[i + 2]
                reading_number = data[i + 3]
                csv_file.write(
                    f"{v_reading}, {time_stamp}, {source_current}, {reading_number}\n"
                )
                csv_file.flush()

            csv_file.write("\n\nRaw Reading from 2182A\n")
            for i in range(0, len(raw_reading), 4):
                v_reading = raw_reading[i]
                time_stamp = raw_reading[i + 1]
                source_current = raw_reading[i + 2]
                reading_number = raw_reading[i + 3]
                csv_file.write(
                    f"{v_reading}, {time_stamp}, {source_current}, {reading_number}\n"
                )

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

    stop_time = time.time()  # Stop the timer...
    # Notify the user of completion and the data streaming rate achieved.
    print("done")
    print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")
    broom.close()

if __name__ == "__main__":
    main()
    sys.exit(0)
