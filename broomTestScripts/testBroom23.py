import pyvisa
import asyncio
import matplotlib.pyplot as plt
import csv
import logging

logging.basicConfig(level=logging.DEBUG)

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
        self.sweep_interval = 10  # Increased time between sweeps

    async def connect_instruments(self):
        try:
            self.k6221 = self.rm.open_resource("TCPIP0::169.254.47.133::1394::SOCKET")
            self.k6221.write_termination = '\n'
            self.k6221.read_termination = '\n'
            self.k6221.timeout = 30000  # Increased timeout to 30 seconds
            await self.write_and_wait("*RST")
            await asyncio.sleep(1)  # Added delay after reset
            idn = await self.query_async("*IDN?")
            logging.info(f"Connected to 6221: {idn}")

            await self.write_and_wait("SYST:COMM:SER:SEND '*RST'")
            await asyncio.sleep(1)  # Added delay after reset
            idn_2182a = await self.query_2182A("*IDN?")
            logging.info(f"Connected to 2182A: {idn_2182a}")
        except pyvisa.Error as e:
            logging.error(f"Error connecting to instruments: {e}")
            raise

    async def write_and_wait(self, command):
        await self.write_async(command)
        await asyncio.sleep(0.1)  # Added small delay after each command
        await self.wait_for_opc()

    async def wait_for_opc(self):
        for _ in range(100):  # Limit the number of retries
            response = await self.query_async("*OPC?")
            if response.strip() == "1":
                return
            await asyncio.sleep(0.1)
        raise TimeoutError("Operation did not complete in time")

    async def configure_instruments(self):
        # Configure 6221
        await self.write_and_wait("SOUR:PDEL:RANG BEST")
        await self.write_and_wait("SOUR:PDEL:SWE ON")
        await self.write_and_wait("SOUR:SWE:SPAC LIN")

        # Configure 2182A
        await self.write_2182A_and_wait("SENS:FUNC 'VOLT'")
        await self.write_2182A_and_wait("SENS:VOLT:RANG:AUTO ON")
        await self.write_2182A_and_wait("SENS:VOLT:NPLC 0.01")
        await self.write_2182A_and_wait("TRIG:SOUR EXT")
        await self.write_2182A_and_wait("TRIG:DEL 0")
        await self.write_2182A_and_wait("TRIG:COUN 11")

        # Set up trigger link
        await self.write_and_wait("TRIG:SOUR TLINK")
        await self.write_and_wait("TRIG:DIR SOUR")
        await self.write_and_wait("TRIG:OUTP DEL")
        await self.write_and_wait("TRIG:ILIN 1")
        await self.write_and_wait("TRIG:OLIN 2")

    async def arm_instruments(self):
        await self.write_2182A_and_wait("INIT")
        await self.write_and_wait("SOUR:PDEL:ARM")
        await asyncio.sleep(0.5)  # Increased delay after arming

    async def set_sweep_parameters(self):
        await self.write_and_wait(f"SOUR:CURR:START {self.start_current}")
        await self.write_and_wait(f"SOUR:CURR:STOP {self.stop_current}")
        await self.write_and_wait(f"SOUR:CURR:STEP {self.step_current}")
        await self.write_and_wait(f"SOUR:PDEL:WIDTH {self.pulse_width}")
        await self.write_and_wait(f"SOUR:PDEL:SDEL {self.pulse_delay}")

    async def run_sweep(self):
        try:
            await self.configure_instruments()
            await self.arm_instruments()
            await self.write_and_wait("INIT")

            # Wait for sweep to complete
            await asyncio.sleep(2)  # Initial delay
            for _ in range(100):  # Limit the number of retries
                if await self.is_sweep_complete():
                    break
                await asyncio.sleep(0.5)
            else:
                raise TimeoutError("Sweep did not complete in time")

            current_data = await self.query_async_values("TRAC:DATA?")
            voltage_data = await self.query_2182A_values("TRAC:DATA?")

            return current_data, voltage_data
        except Exception as e:
            logging.error(f"Error during sweep: {e}")
            await self.abort_sweep()
            raise
        finally:
            await self.reset_instruments()

    async def is_sweep_complete(self):
        status = int(await self.query_async("STAT:OPER:COND?"))
        return (status & 0x1000) == 0

    async def abort_sweep(self):
        await self.write_async("SOUR:SWE:ABOR")
        await self.write_2182A("ABOR")

    async def reset_instruments(self):
        await self.write_and_wait("*RST")
        await self.write_2182A_and_wait("*RST")

    async def write_async(self, command):
        logging.debug(f"Sending to 6221: {command}")
        await asyncio.get_event_loop().run_in_executor(None, self.k6221.write, command)

    async def query_async(self, query):
        logging.debug(f"Querying 6221: {query}")
        return await asyncio.get_event_loop().run_in_executor(None, self.k6221.query, query)

    async def query_async_values(self, query):
        logging.debug(f"Querying 6221 values: {query}")
        return await asyncio.get_event_loop().run_in_executor(None, self.k6221.query_ascii_values, query)

    async def write_2182A(self, command):
        logging.debug(f"Sending to 2182A: {command}")
        await self.write_async(f"SYST:COMM:SER:SEND '{command}'")

    async def write_2182A_and_wait(self, command):
        await self.write_2182A(command)
        await self.wait_for_2182A_opc()

    async def wait_for_2182A_opc(self):
        for _ in range(100):  # Limit the number of retries
            response = await self.query_2182A("*OPC?")
            if response.strip() == "1":
                return
            await asyncio.sleep(0.1)
        raise TimeoutError("2182A operation did not complete in time")

    async def query_2182A(self, query):
        logging.debug(f"Querying 2182A: {query}")
        await self.write_2182A(query)
        return await self.query_async("SYST:COMM:SER:ENT?")

    async def query_2182A_values(self, query):
        response = await self.query_2182A(query)
        return [float(x) for x in response.split(',')]

    async def process_data(self):
        self.currents, self.voltages = await self.run_sweep()
        # Add any additional data processing here

    async def save_data(self):
        try:
            with open('pulsed_iv_sweep.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Current (A)', 'Voltage (V)'])
                for current, voltage in zip(self.currents, self.voltages):
                    writer.writerow([current, voltage])
            logging.info("Data saved to pulsed_iv_sweep.csv")
        except IOError as e:
            logging.error(f"Error saving data: {e}")

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
                await self.process_data()
                await self.save_data()
                self.plot_data()
                await asyncio.sleep(self.sweep_interval)
            except Exception as e:
                logging.error(f"Error during monitoring: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def run(self):
        try:
            await self.connect_instruments()
            await self.set_sweep_parameters()
            await self.monitor_sweep()
        except Exception as e:
            logging.error(f"An error occurred during the sweep: {e}")
        finally:
            if self.k6221:
                self.k6221.close()
            self.rm.close()

if __name__ == "__main__":
    sweep = PulsedIVSweep()
    asyncio.run(sweep.run())