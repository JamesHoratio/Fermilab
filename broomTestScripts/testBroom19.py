import pyvisa
import time
import csv
import matplotlib.pyplot as plt

class PulsedIVSweep:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.k6221 = None
        self.start_current = 0
        self.stop_current = 0
        self.step_current = 0
        self.pulse_width = 0
        self.pulse_delay = 0
        self.voltages = []
        self.currents = []

    def connect_instruments(self):
        # Connect to the 6221 via LAN
        self.k6221 = self.rm.open_resource("TCPIP0::169.254.47.133::1394::SOCKET")  # Update IP as needed
        self.k6221.write_termination = '\n'
        self.k6221.read_termination = '\n'
        print(f"Connected to: {self.k6221.query('*IDN?')}")

    def configure_instruments(self):
        # Reset and configure 6221
        self.k6221.write("*RST")
        self.k6221.write("SOUR:PDEL:RANG BEST")
        self.k6221.write("SOUR:PDEL:SWE ON")
        self.k6221.write("SOUR:SWE:SPAC LIN")
        
        # Configure 2182A through 6221
        self.send_to_2182A("*RST")
        self.send_to_2182A("SENS:FUNC 'VOLT'")
        self.send_to_2182A("SENS:VOLT:RANG:AUTO ON")

    def send_to_2182A(self, command):
        self.k6221.write(f"SYST:COMM:SER:SEND '{command}'")
        time.sleep(0.1)  # Allow time for command execution

    def set_sweep_parameters(self):
        self.start_current = float(input("Enter start current (A): "))
        self.stop_current = float(input("Enter stop current (A): "))
        self.step_current = float(input("Enter step current (A): "))
        self.pulse_width = float(input("Enter pulse width (s): "))
        self.pulse_delay = float(input("Enter pulse delay (s): "))

        self.k6221.write(f"SOUR:CURR:START {self.start_current}")
        self.k6221.write(f"SOUR:CURR:STOP {self.stop_current}")
        self.k6221.write(f"SOUR:CURR:STEP {self.step_current}")
        self.k6221.write(f"SOUR:PDEL:WIDTH {self.pulse_width}")
        self.k6221.write(f"SOUR:PDEL:SDEL {self.pulse_delay}")

    def run_sweep(self):
        self.k6221.write("SOUR:PDEL:ARM")
        self.k6221.write("INIT")
        
        # Wait for sweep to complete
        while int(self.k6221.query("STAT:OPER:COND?")) & 8:
            time.sleep(0.5)
        
        # Fetch data
        data = self.k6221.query("TRAC:DATA?").split(',')
        self.voltages = [float(data[i]) for i in range(0, len(data), 2)]
        self.currents = [self.start_current + i * self.step_current for i in range(len(self.voltages))]

    def save_data(self):
        with open('pulsed_iv_sweep.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Current (A)', 'Voltage (V)'])
            for current, voltage in zip(self.currents, self.voltages):
                writer.writerow([current, voltage])

    def plot_data(self):
        plt.figure(figsize=(10, 6))
        plt.plot(self.currents, self.voltages, 'b-')
        plt.title('Pulsed IV Sweep')
        plt.xlabel('Current (A)')
        plt.ylabel('Voltage (V)')
        plt.grid(True)
        plt.show()

    def run(self):
        self.connect_instruments()
        self.configure_instruments()
        self.set_sweep_parameters()
        self.run_sweep()
        self.save_data()
        self.plot_data()

if __name__ == "__main__":
    sweep = PulsedIVSweep()
    sweep.run()