import pyvisa
import time
import csv
import matplotlib.pyplot as plt

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
        try:
            # Reset and configure 6221
            self.k6221.write("*RST")
            self.k6221.write("SOUR:PDEL:RANG BEST")
            self.k6221.write("SOUR:PDEL:SWE ON")
            self.k6221.write("SOUR:SWE:SPAC LIN")
            self.k6221.write("TRIG:SOUR BUS")  # Set to bus trigger

            # Configure 2182A through 6221
            self.send_to_2182A("*RST")
            self.send_to_2182A("SENS:FUNC 'VOLT'")
            self.send_to_2182A("SENS:VOLT:RANG:AUTO ON")
            self.send_to_2182A("TRIG:SOUR BUS")  # Set to bus trigger

            # Additional configuration
            self.k6221.write("SOUR:PDEL:LME 2")  # Enable two-point delta mode
            self.k6221.write("TRAC:CLE")  # Clear buffer
            self.k6221.write("TRAC:POIN 1000")  # Set buffer size

            # Set sweep parameters
            self.k6221.write(f"SOUR:CURR:START {self.start_current}")
            self.k6221.write(f"SOUR:CURR:STOP {self.stop_current}")
            self.k6221.write(f"SOUR:CURR:STEP {self.step_current}")
            self.k6221.write(f"SOUR:PDEL:WIDTH {self.pulse_width}")
            self.k6221.write(f"SOUR:PDEL:SDEL {self.pulse_delay}")

            print("Instruments configured successfully.")
        except pyvisa.Error as e:
            print(f"Error configuring instruments: {e}")
            raise
    
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
            self.k6221.write("SOUR:PDEL:ARM")
            time.sleep(1)  # Wait for arm to complete
            
            if not self.user_check():
                print("Sweep aborted by user.")
                return
            
            # Trigger both instruments
            self.k6221.write("*TRG")
            self.send_to_2182A("*TRG")
            
            # Wait for sweep to complete
            while True:
                status_6221 = int(self.k6221.query("STAT:OPER:COND?").strip())
                status_2182a = int(self.send_to_2182A_with_response("STAT:OPER:COND?"))
                
                # Check if both instruments are idle
                if (status_6221 & 0x1000) == 0 and (status_2182a & 0x1000) == 0:
                    break
                time.sleep(0.5)
            
            # Ensure the sweep is completely finished
            time.sleep(1)
            
            # Fetch data
            data = self.k6221.query("TRAC:DATA?").strip().split(',')
            if len(data) < 2:
                raise ValueError("No data received from the instrument")
            
            self.voltages = [float(data[i]) for i in range(0, len(data), 2) if data[i]]
            self.currents = [self.start_current + i * self.step_current for i in range(len(self.voltages))]
            
            print(f"Sweep completed. {len(self.voltages)} data points collected.")
            
            # Reset instruments for next sweep
            self.reset_instruments()
        except (pyvisa.Error, ValueError) as e:
            print(f"Error during sweep: {e}")
            raise

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

    def reset_instruments(self):
        try:
            self.k6221.write("*RST")
            self.send_to_2182A("*RST")
            print("Instruments reset successfully.")
        except pyvisa.Error as e:
            print(f"Error resetting instruments: {e}")
            raise
    
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