import pyvisa
import time
import csv
import matplotlib.pyplot as plt
import logging
import datetime
import numpy as np
import argparse
import sys
import os
import asyncio


class PulsedIVSweep:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.k6221 = None
        self.start_current = 0
        self.stop_current = 0.01
        self.step_current = 0.001
        self.pulse_width = 0.00005
        self.pulse_delay = 0.00005
        self.voltages = []
        self.currents = []

    def connect_instruments(self):
        try:
            self.k6221 = self.rm.open_resource("TCPIP0::169.254.47.133::1394::SOCKET")
            self.k6221.write_termination = '\n'
            self.k6221.read_termination = '\n'
            self.k6221.timeout = 20000  # 20 seconds timeout
            print(f"Connected to 6221: {self.k6221.query('*IDN?').strip()}")

            # Configure and check 2182A
            idn_2182a = self.send_to_2182A_with_response("*IDN?")
            print(f"Connected to 2182A: {idn_2182a}")
        except pyvisa.Error as e:
            print(f"Error connecting to instruments: {e}")
            raise

    def configure_instruments(self):
        # Configure 6221
        self.k6221.write("*RST")
        self.k6221.write("SOUR:PDEL:RANG BEST")
        self.k6221.write("SOUR:PDEL:SWE ON")
        self.k6221.write("SOUR:SWE:SPAC LIN")

        # Configure 2182A
        self.send_to_2182A("*RST")
        self.send_to_2182A("SENS:FUNC 'VOLT'")
        self.send_to_2182A("SENS:VOLT:RANG:AUTO ON")
        self.send_to_2182A("SENS:VOLT:NPLC 0.01")  # Fast integration time
        self.send_to_2182A("TRIG:SOUR EXT")
        self.send_to_2182A("TRIG:DEL 0")
        self.send_to_2182A("TRIG:COUN 11")  # Match number of pulses

        # Set up trigger link
        self.k6221.write("TRIG:SOUR TLINK")
        self.k6221.write("TRIG:DIR SOUR")
        self.k6221.write("TRIG:OUTP DEL")
        self.k6221.write("TRIG:ILIN 1")
        self.k6221.write("TRIG:OLIN 2")

    def arm_instruments(self):
        self.send_to_2182A("INIT")
        self.k6221.write("SOUR:PDEL:ARM")
        time.sleep(0.1)  # Short delay to ensure both instruments are ready
    
    def user_check(self):
        while True:
            response = input("Ready to start the sweep? (y/n): ").lower()
            if response == 'y':
                return True
            elif response == 'n':
                return False
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

    def send_to_2182A(self, command):
        self.k6221.write(f"SYST:COMM:SER:SEND '{command}'")
        time.sleep(0.1)  # Allow time for command execution
    
    def send_to_2182A_with_response(self, command):
        self.k6221.write(f"SYST:COMM:SER:SEND '{command}'")
        time.sleep(0.1)  # Allow time for command execution
        return self.k6221.query("SYST:COMM:SER:ENT?").strip()

    def set_sweep_parameters(self):
        #self.start_current = float(input("Enter start current (A): "))
        #self.stop_current = float(input("Enter stop current (A): "))
        #self.step_current = float(input("Enter step current (A): "))
        #self.pulse_width = float(input("Enter pulse width (s): "))
        #self.pulse_delay = float(input("Enter pulse delay (s): "))

        self.k6221.write(f"SOUR:CURR:START {self.start_current}")
        self.k6221.write(f"SOUR:CURR:STOP {self.stop_current}")
        self.k6221.write(f"SOUR:CURR:STEP {self.step_current}")
        self.k6221.write(f"SOUR:PDEL:WIDTH {self.pulse_width}")
        self.k6221.write(f"SOUR:PDEL:SDEL {self.pulse_delay}")

    def run_sweep(self):
        try:
            self.configure_instruments()
            self.arm_instruments()
            self.k6221.write("INIT")

            # Wait for sweep completion
            while int(self.k6221.query("STAT:OPER:COND?")) & 0x1000:
                time.sleep(0.1)

            # Collect data from 6221
            current_data = self.k6221.query_ascii_values("TRAC:DATA?")

            # Collect data from 2182A
            voltage_data = self.query_2182A_ascii_values("TRAC:DATA?")

            return current_data, voltage_data
        except Exception as e:
            logging.error(f"Error during sweep: {e}")
            self.abort_sweep()
            raise
        finally:
            self.reset_instruments()

    def abort_sweep(self):
        self.k6221.write("SOUR:SWE:ABOR")
        self.send_to_2182A("ABOR")

    def reset_instruments(self):
        self.k6221.write("*RST")
        self.send_to_2182A("*RST")

    async def process_data(self):
        self.currents, self.voltages = await self.run_synchronized_sweep()

    async def handle_error(self, e):
        print(f"An error occurred during the sweep: {e}")
        await self.abort_sweep()

    def save_data(self):
        try:
            with open('pulsed_iv_sweep.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Current (A)', 'Voltage (V)'])
                for current, voltage in zip(self.currents, self.voltages):
                    writer.writerow([current, voltage])
            print("Data saved to pulsed_iv_sweep.csv")
        except IOError as e:
            print(f"Error saving data: {e}")

    #def reset_instruments(self):
    #    try:
    #        self.k6221.write("*RST")
    #        self.send_to_2182A("*RST")
    #        print("Instruments reset successfully.")
    #    except pyvisa.Error as e:
    #        print(f"Error resetting instruments: {e}")
    #        raise

    def configure_trigger_link(self):
        # Configure 6221 as trigger source
        self.k6221.write("TRIG:SOUR TLINK")
        self.k6221.write("TRIG:DIR SOUR")
        self.k6221.write("TRIG:OUTP DEL")
        self.k6221.write("TRIG:ILIN 1")
        self.k6221.write("TRIG:OLIN 2")

        # Configure 2182A as trigger recipient
        self.send_to_2182A("TRIG:SOUR TLINK")
        self.send_to_2182A("TRIG:ILIN 2")
        self.send_to_2182A("TRIG:OLIN 1")

    async def run_synchronized_sweep(self):
        self.configure_trigger_link()
        self.configure_instruments()
        self.arm_instruments()

        # Start the sweep
        self.k6221.write("INIT")

        # Wait for completion
        while int(self.k6221.query("STAT:OPER:COND?")) & 0x1000:
            time.sleep(0.1)

        # Collect data
        current_data = self.k6221.query_ascii_values("TRAC:DATA?")
        voltage_data = self.query_2182A_ascii_values("TRAC:DATA?")

        return current_data, voltage_data
    
    def plot_data(self):
        plt.figure(figsize=(10, 6))
        plt.plot(self.currents, self.voltages, 'b-')
        plt.title('Pulsed IV Sweep')
        plt.xlabel('Current (A)')
        plt.ylabel('Voltage (V)')
        plt.grid(True)
        plt.show()

    def run(self):
        try:
            self.connect_instruments()
            self.configure_instruments()
            self.set_sweep_parameters()
            self.user_check()
            self.run_sweep()
            self.save_data()
            self.reset_instruments()
            self.plot_data()
        except Exception as e:
            print(f"An error occurred during the sweep: {e}")
        finally:
            if self.k6221:
                self.k6221.close()
            self.rm.close()

if __name__ == "__main__":
    sweep = PulsedIVSweep()
    sweep.run()