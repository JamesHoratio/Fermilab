import sys
import os
import csv
import time
import datetime
import pyvisa as visa
import argparse
import tkinter as tk
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import threading
import queue
import logging
import re
from keithley2600 import Keithley2600
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

DEBUG_PRINT_COMMANDS = True
INSTRUMENT_RESOURCE_STRING_6221 = 'TCPIP0::169.254.47.133::1394::SOCKET'
INSTRUMENT_RESOURCE_STRING_2182A = 'GPIB0::7::INSTR'
SAVED_PARAMETERS_FILENAME = "sweep_parameters.txt"

class K6221:
    def __init__(self):
        self.K6221Address = INSTRUMENT_RESOURCE_STRING_6221
        self.connected = self.connect()
        if self.connected:
            self.sm.write_termination = '\n'
            self.sm.read_termination = '\n'
            self.sm.chunk_size = 102400
            self.sm.write(':SYST:PRES')
            time.sleep(1)
            self.sm.write('FORM:ELEM READ')
            self.sm.write(':SYST:COMM:SER:BAUD 19200')
            self.sm.write(':SYST:COMM:SER:SEND "*RST"')
            time.sleep(1)
            self.sm.write(':SYST:COMM:SER:SEND "*CLS"')
            time.sleep(0.2)
            self.sm.write(':SYST:COMM:SER:SEND ":INIT:CONT OFF;:ABORT"')
            time.sleep(0.2)
            self.sm.write(':SYST:COMM:SER:SEND ":SYST:BEEP:STAT OFF"')
            time.sleep(0.2)
            self.sm.write('SYST:COMM:SER:SEND "FORM:ELEM READ"')
            time.sleep(0.2)

    def connect(self):
        try:
            self.rm = visa.ResourceManager()
            self.sm = self.rm.open_resource(self.K6221Address, write_termination='\n', read_termination='\n')
            logging.debug(f'Connected to 6221 at {self.K6221Address}')
            return True
        except Exception:
            logging.error(f'Unable to connect to 6221 at {self.K6221Address}')
            return False

    def setSourceMode(self, chan, param, slim, comp):
        self.sm.write(':SOUR:SWE:ABOR')
        if slim.lower() == 'auto':
            self.sm.write('SOUR:CURR:RANG:AUTO ON')
        else:
            self.sm.write('SOUR:CURR:RANG ' + slim)
        if comp.lower() == 'auto':
            self.sm.write('SOUR:CURR:COMP ' + str(100))
        else:
            self.sm.write('SOUR:CURR:COMP ' + comp)
        self.sm.write(':OUTP ON')

    def setSenseMode(self, chan, param, mlim, nplc, aver):
        self.sm.write(':SYST:CLE')
        self.sm.write(':SYST:COMM:SER:SEND "SENS:CHAN 1"')
        time.sleep(0.2)
        self.sm.write(':SYST:COMM:SER:SEND "SENS:FUNC \'VOLT:DC\'"')
        time.sleep(0.2)
        self.sm.write(':SYST:COMM:SER:SEND "SENS:VOLT:NPLC ' + str(nplc) + '"')
        time.sleep(0.2)
        self.sm.write(':SYST:COMM:SER:SEND ":TRAC:CLE"')
        time.sleep(0.2)
        if mlim.lower() == 'auto':
            self.sm.write('SYST:COMM:SER:SEND "SENS:VOLT:RANG:AUTO ON"')
        else:
            self.sm.write('SYST:COMM:SER:SEND "SENS:VOLT:RANG ' + mlim + '"')
        time.sleep(0.2)
        self.sm.write(':SYST:COMM:SER:SEND ":SAMP:COUN ' + str(aver) + '"')

    def IVSweep(self, dcivData):
        start = float(dcivData["sStart"])
        stop = float(dcivData["sEnd"])
        points = int(dcivData["sPoints"])
        loop = dcivData["Loop"]
        LoopBiDir = dcivData["LoopBiDir"]
        aver = int(dcivData["aver"])
        nplc = float(dcivData["nplc"])
        sourceLimit = dcivData["slimit"]
        measureLimit = dcivData["mlimit"]
        stepPeriod = dcivData["sDel"]
        pWidth = dcivData["pWidth"]
        pPeriod = dcivData["pPeriod"]
        pulse = dcivData["Pulse"]

        self.sm.write(':SOUR:SWE:ABOR')
        self.setSourceMode('1', 'I', sourceLimit, measureLimit)
        self.setSenseMode('1', 'V', measureLimit, nplc, aver)

        if loop:
            if LoopBiDir:
                sweepList = np.concatenate([np.linspace(0, stop, points), np.linspace(stop, 0, points), np.linspace(0, -stop, points), np.linspace(-stop, 0, points)])
            else:
                sweepList = np.concatenate([np.linspace(start, stop, points), np.linspace(stop, start, points)])
        else:
            sweepList = np.linspace(start, stop, points)
        tPoints = len(sweepList)
        logging.info('sweep list' + str(sweepList))
        currStep = (stop - start) / points
        self.sm.write(':SOUR:SWE:SPAC LIST')
        self.sm.write(':SOUR:SWE:RANG AUTO')
        self.sm.write(':SOUR:SWE:CAB OFF')

        self.sm.write(':TRAC:CLE')
        self.sm.write(':TRAC:FEED SENS')
        self.sm.write(':TRAC:FEED:CONT NEXT')
        self.sm.write(':TRAC:POIN ' + str(tPoints))
        if pulse:
            self.sm.write('SOUR:LIST:CURR ' + str(start))
            self.sm.write('SOUR:LIST:DEL ' + str(pPeriod))
            for i in range(1, tPoints):
                self.sm.write('SOUR:LIST:CURR:APP ' + str(sweepList[i]))
                self.sm.write('SOUR:LIST:DEL:APP ' + str(pPeriod))
            self.sm.write(':SOUR:SWE:RANG BEST')
            self.sm.write(':SOUR:PDEL:WIDT ' + str(pWidth))
            self.sm.write(':SOUR:PDEL:SDEL 100E-6')
            self.sm.write(':SOUR:PDEL:LOW 0')
            self.sm.write(':SOUR:PDEL:SWE ON')
            self.sm.write(':SOUR:PDEL:LME 2')
            self.sm.write(':SOUR:PDEL:ARM')
            time.sleep(1)
            self.sm.write(':INIT:IMM')
            time.sleep(tPoints * (float(pPeriod) + float(pWidth) + 0.1) + 5)
            self.sm.write('SOUR:SWE:ABOR')
            values = self.getTraceData('1', 'I', tPoints)
        else:
            self.sm.write('SOUR:LIST:CURR ' + str(start))
            self.sm.write('SOUR:LIST:DEL ' + str(stepPeriod))
            for i in range(1, tPoints):
                self.sm.write('SOUR:LIST:CURR:APP ' + str(sweepList[i]))
                self.sm.write('SOUR:LIST:DEL:APP ' + str(stepPeriod))
            self.sm.write(':SOUR:SWE:RANG BEST')
            self.sm.write(':TRIG:SOUR TLINK')
            self.sm.write(':TRIG:DIR SOUR')
            self.sm.write(':TRIG:OLIN 2')
            self.sm.write(':TRIG:ILIN 1')
            self.sm.write(':TRIG:OUTP DEL')
            self.sm.write(':TRAC:CLE')
            self.sm.write(':SYST:COMM:SER:SEND ":SENS:VOLT:LPAS OFF"')
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":SENS:VOLT:DFIL OFF"')
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRAC:CLE"')
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRAC:FEED SENS"')
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRAC:POIN ' + str(tPoints) + '"')
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRIG:SOUR EXT"')
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRIG:COUN ' + str(tPoints) + '"')
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRAC:FEED:CONT NEXT"')
            time.sleep(0.1)
            self.sm.write(':SOUR:SWE:ARM')
            time.sleep(1)
            self.sm.write(':INIT:IMM')
            self.sm.write(':SYST:COMM:SER:SEND ":INIT"')
            time.sleep(tPoints * (float(stepPeriod) + 0.1) + 5)
            self.sm.write('SOUR:SWE:ABOR')
            self.turnOffOutputs()
            time.sleep(1)
            values = self.get2182TraceData('1', 'I', tPoints)
        print(values)
        logging.info('got these values\n' + str(values))
        measuredValues = resultBook()
        measuredValues.points = len(values)
        measuredValues.I = sweepList
        measuredValues.V = values

        return measuredValues

    def getTraceData(self, smu, param, tPoints):
        mData = []
        waitingForData = True
        timeSlept = 0
        while waitingForData:
            if len(mData) >= tPoints:
                logging.info('got all Data')
                waitingForData = False
            elif timeSlept > 30:
                logging.warning('timed out. Leaving with either empty or partial data of length ' + str(len(mData)))
                waitingForData = False
            else:
                try:
                    resp = self.sm.query(':TRAC:DATA?')
                    mData = np.append(mData, np.asarray(re.findall('[+-][0-9\.]+E[+-][0-9]+', resp), dtype=float))
                    logging.info('Adding data' + resp)
                except Exception as e:
                    logging.warning('Unable to add the data. Got this  ' + resp)
                timeSlept += 0.5
                time.sleep(0.5)
        return mData

    def get2182TraceData(self, smu, param, tPoints):
        mData = []
        time.sleep(5)
        self.sm.write(':SYST:COMM:SER:SEND ":TRAC:DATA?"')
        time.sleep(1)
        waitingForData = True
        timeSlept = 0
        while waitingForData:
            if len(mData) >= tPoints:
                logging.info('got all Data')
                waitingForData = False
            elif timeSlept > 10:
                logging.warning('timed out')
                waitingForData = False
            else:
                try:
                    time.sleep(0.2)
                    resp = self.sm.query(':SYST:COMM:SER:ENT?')
                    logging.info('Read from instrument: ' + resp)
                    mData = np.append(mData, np.asarray(re.findall('[+-][0-9\.]+E[+-][0-9]+', resp), dtype=float))
                    logging.info('Adding data' + resp)
                except ValueError:
                    logging.warning('Unable to add the data' + resp)
                timeSlept += 0.5
                time.sleep(0.3)
        return mData

    def turnOffOutputs(self):
        self.sm.write(':OUTP OFF')

class resultBook:
    def __init__(self):
        logging.info('A result book is created')

class Broom:
    def __init__(self):
        try:
            self.rm = visa.ResourceManager()
            self.device_6221 = self.connect_instrument(INSTRUMENT_RESOURCE_STRING_6221, '\r', '\n')
            self.device_2182A = self.connect_instrument(INSTRUMENT_RESOURCE_STRING_2182A, '\r', '\n')
            response_6221 = self.device_6221.query('*IDN?')
            response_2182A = self.device_2182A.query('*IDN?')
            print("6221 ID:", response_6221)
            print("2182A ID:", response_2182A)
        except visa.VisaIOError as e:
            print(f"Error initializing instruments: {e}")
            sys.exit(1)

    def connect_instrument(self, resource_string, write_termination, read_termination):
        try:
            instrument = self.rm.open_resource(resource_string, write_termination=write_termination, read_termination=read_termination)
            instrument.timeout = 10000
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
            response = device.query(command)
            if DEBUG_PRINT_COMMANDS:
                print(f"Response: {response}")
            return response
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
            self.send_command(self.device_6221, ":SOUR:SWE:ABOR")
            self.send_command(self.device_6221, ":SOUR:WAVE:ABOR")
            self.send_command(self.device_6221, "*RST")
            time.sleep(7)

            if self.query_command(self.device_6221, "*OPC?").strip() != "1":
                print("6221 did not reset properly.")
                sys.exit(1)

            self.send_command(self.device_2182A, "*RST")
            time.sleep(5)

            if self.query_command(self.device_2182A, "*OPC?").strip() != "1":
                print("2182A did not reset properly.")
                sys.exit(1)

            self.send_command(self.device_6221, "pdel:swe ON")
            self.send_command(self.device_6221, ":form:elem READ,TST,RNUM,SOUR")
            time.sleep(1)
            self.send_command(self.device_6221, ":sour:swe:spac LIN")
            self.send_command(self.device_6221, ":sour:curr:start 0")
            self.send_command(self.device_6221, ":sour:curr:stop 0.01")
            self.send_command(self.device_6221, ":sour:curr:poin 11")
            self.send_command(self.device_6221, ":sour:del 0.01")
            self.send_command(self.device_6221, ":sour:swe:rang BEST")
            self.send_command(self.device_6221, ":sour:pdel:lme 2")
            self.send_command(self.device_6221, ":sour:curr:comp 100")
            self.send_command(self.device_2182A, ":sens:volt:rang 10")
            self.send_command(self.device_6221, "UNIT V")
            time.sleep(1)
            self.send_command(self.device_6221, ":sour:swe:arm")
            time.sleep(3)
            self.armquery()
        except Exception as e:
            print(f"Error in device primer: {e}")

    def armquery(self):
        try:
            arm_status = self.query_command(self.device_6221, ":sour:swe:arm:stat?")
            print(f"Pulse sweep armed: {arm_status}")
            return arm_status
        except Exception as e:
            print(f"Error querying arm status: {e}")
            return ""

    def sweep(self):
        try:
            self.send_command(self.device_6221, ":init:imm")
            print("Pulse sweep initiated.")
            time.sleep(4)
        except Exception as e:
            print(f"Error initiating sweep: {e}")

    def get_data_points(self):
        try:
            data_points = int(self.query_command(self.device_6221, ":TRAC:POIN:ACT?").strip())
            print(f"Data points available: {data_points}")
            return data_points
        except Exception as e:
            print(f"Error querying data points: {e}")
            return 0

    def read(self):
        try:
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
            filename = "pulsesweepdata.csv"
            with open(filename, "w", newline='') as file:
                writer = csv.writer(file)
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
            sweep_running = self.query_command(self.device_6221, ":sour:swe:stat?")
            print(f"Pulse sweep running: {sweep_running}")
            return sweep_running
        except Exception as e:
            print(f"Error checking sweep status: {e}")
            return ""

    def usercheck(self):
        user_decision = input("Do you want to continue with Broom? (yes/no): ")
        if user_decision.lower() == "no":
            print("Aborting the Broom as per user's request.")
            self.send_command(self.device_6221, ":SOUR:SWE:ABORT")
            self.testreset()
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

#### initiate logging ###########
logging.basicConfig(filename= "logFile.txt", filemode='a', format='%(asctime)s - %(levelname)s -%(message)s', level=logging.INFO)
logging.info('Logging is started')
root = tk.Tk()
window = MainWindow(root)
root.mainloop()
logging.info('Logging ended')
