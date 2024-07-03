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
        self.sweep_interval = 1  # Time between sweeps in seconds

    async def connect_instruments(self):
        try:
            self.k6221 = self.rm.open_resource("TCPIP0::169.254.47.133::1394::SOCKET")
            self.k6221.write_termination = '\n'
            self.k6221.read_termination = '\n'
            self.k6221.timeout = 20000  # 20 seconds timeout
            print(f"Connected to 6221: {await self.query_async(self.k6221, '*IDN?')}")

            # Configure and check 2182A
            idn_2182a = await self.send_to_2182A_with_response("*IDN?")
            print(f"Connected to 2182A: {idn_2182a}")
        except pyvisa.Error as e:
            print(f"Error connecting to instruments: {e}")
            raise

    async def configure_instruments(self):
        # Configure 6221
        await self.write_async(self.k6221, "*RST")
        await self.write_async(self.k6221, "SOUR:PDEL:RANG BEST")
        await self.write_async(self.k6221, "SOUR:PDEL:SWE ON")
        await self.write_async(self.k6221, "SOUR:SWE:SPAC LIN")

        # Configure 2182A
        await self.send_to_2182A("*RST")
        await self.send_to_2182A("SENS:FUNC 'VOLT'")
        await self.send_to_2182A("SENS:VOLT:RANG:AUTO ON")
        await self.send_to_2182A("SENS:VOLT:NPLC 0.01")  # Fast integration time
        await self.send_to_2182A("TRIG:SOUR EXT")
        await self.send_to_2182A("TRIG:DEL 0")
        await self.send_to_2182A("TRIG:COUN 11")  # Match number of pulses

        # Set up trigger link
        await self.write_async(self.k6221, "TRIG:SOUR TLINK")
        await self.write_async(self.k6221, "TRIG:DIR SOUR")
        await self.write_async(self.k6221, "TRIG:OUTP DEL")
        await self.write_async(self.k6221, "TRIG:ILIN 1")
        await self.write_async(self.k6221, "TRIG:OLIN 2")

    async def arm_instruments(self):
        await self.send_to_2182A("INIT")
        await self.write_async(self.k6221, "SOUR:PDEL:ARM")
        await asyncio.sleep(0.1)  # Short delay to ensure both instruments are ready

    async def user_check(self):
        while True:
            response = input("Ready to start the sweep? (y/n): ").lower()
            if response == 'y':
                return True
            elif response == 'n':
                return False
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

    async def send_to_2182A(self, command):
        await self.write_async(self.k6221, f"SYST:COMM:SER:SEND '{command}'")
        await asyncio.sleep(0.1)  # Allow time for command execution

    async def send_to_2182A_with_response(self, command):
        await self.write_async(self.k6221, f"SYST:COMM:SER:SEND '{command}'")
        await asyncio.sleep(0.1)  # Allow time for command execution
        return await self.query_async(self.k6221, "SYST:COMM:SER:ENT?")

    async def set_sweep_parameters(self):
        await self.write_async(self.k6221, f"SOUR:CURR:START {self.start_current}")
        await self.write_async(self.k6221, f"SOUR:CURR:STOP {self.stop_current}")
        await self.write_async(self.k6221, f"SOUR:CURR:STEP {self.step_current}")
        await self.write_async(self.k6221, f"SOUR:PDEL:WIDTH {self.pulse_width}")
        await self.write_async(self.k6221, f"SOUR:PDEL:SDEL {self.pulse_delay}")

    async def run_sweep(self):
        try:
            await self.configure_instruments()
            await self.arm_instruments()
            await self.write_async(self.k6221, "INIT")

            # Wait for sweep completion
            while int(await self.query_async(self.k6221, "STAT:OPER:COND?")) & 0x1000:
                await asyncio.sleep(0.1)

            # Collect data from 6221
            current_data = await self.query_async_values(self.k6221, "TRAC:DATA?")

            # Collect data from 2182A
            voltage_data = await self.query_2182A_ascii_values("TRAC:DATA?")

            return current_data, voltage_data
        except Exception as e:
            logging.error(f"Error during sweep: {e}")
            await self.abort_sweep()
            raise
        finally:
            await self.reset_instruments()

    async def abort_sweep(self):
        await self.write_async(self.k6221, "SOUR:SWE:ABOR")
        await self.send_to_2182A("ABOR")

    async def reset_instruments(self):
        await self.write_async(self.k6221, "*RST")
        await self.send_to_2182A("*RST")

    async def process_data(self):
        self.currents, self.voltages = await self.run_synchronized_sweep()
        # Add any additional data processing here

    async def handle_error(self, e):
        print(f"An error occurred during the sweep: {e}")
        await self.abort_sweep()

    async def save_data(self):
        try:
            with open('pulsed_iv_sweep.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Current (A)', 'Voltage (V)'])
                for current, voltage in zip(self.currents, self.voltages):
                    writer.writerow([current, voltage])
            print("Data saved to pulsed_iv_sweep.csv")
        except IOError as e:
            print(f"Error saving data: {e}")

    async def configure_trigger_link(self):
        # Configure 6221 as trigger source
        await self.write_async(self.k6221, "TRIG:SOUR TLINK")
        await self.write_async(self.k6221, "TRIG:DIR SOUR")
        await self.write_async(self.k6221, "TRIG:OUTP DEL")
        await self.write_async(self.k6221, "TRIG:ILIN 1")
        await self.write_async(self.k6221, "TRIG:OLIN 2")

        # Configure 2182A as trigger recipient
        await self.send_to_2182A("TRIG:SOUR TLINK")
        await self.send_to_2182A("TRIG:ILIN 2")
        await self.send_to_2182A("TRIG:OLIN 1")

    async def run_synchronized_sweep(self):
        await self.configure_trigger_link()
        await self.configure_instruments()
        await self.arm_instruments()

        # Start the sweep
        await self.write_async(self.k6221, "INIT")

        # Wait for completion
        while int(await self.query_async(self.k6221, "STAT:OPER:COND?")) & 0x1000:
            await asyncio.sleep(0.1)

        # Collect data
        current_data = await self.query_async_values(self.k6221, "TRAC:DATA?")
        voltage_data = await self.query_2182A_ascii_values("TRAC:DATA?")

        return current_data, voltage_data

    def plot_data(self):
        plt.figure(figsize=(10, 6))
        plt.plot(self.currents, self.voltages, 'b-')
        plt.title('Pulsed IV Sweep')
        plt.xlabel('Current (A)')
        plt.ylabel('Voltage (V)')
        plt.grid(True)
        plt.show()

    async def monitor_sweep(self):
        while True:
            try:
                await self.run_synchronized_sweep()
                await self.process_data()
                await self.save_data()
                self.plot_data()
                await asyncio.sleep(self.sweep_interval)
            except Exception as e:
                await self.handle_error(e)

    async def write_async(self, instrument, command):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, instrument.write, command)

    async def query_async(self, instrument, query):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, instrument.query, query)

    async def query_async_values(self, instrument, query):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, instrument.query_ascii_values, query)

    async def query_2182A_ascii_values(self, query):
        await self.send_to_2182A(query)
        response = await self.query_async(self.k6221, "SYST:COMM:SER:ENT?")
        return [float(x) for x in response.split(',')]

    async def run(self):
        try:
            await self.connect_instruments()
            await self.configure_instruments()
            await self.set_sweep_parameters()
            if await self.user_check():
                await self.monitor_sweep()
        except Exception as e:
            print(f"An error occurred during the sweep: {e}")
        finally:
            if self.k6221:
                self.k6221.close()
            self.rm.close()

if __name__ == "__main__":
    sweep = PulsedIVSweep()
    asyncio.run(sweep.run())