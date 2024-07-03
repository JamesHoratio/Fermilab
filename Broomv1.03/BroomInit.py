import json
import pyvisa
import time
import numpy as np


file_path = 'instrument_config.json'
class InstrumentSetup:
    file_path = 'instrument_config.json'
    def __init__(self, file_path):
        config = self.load_config(file_path)
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(self.config['6221']['address'])
        self.inst.timeout = 20000
        self.inst.write_termination = '\n'
        self.inst.read_termination = '\n'
        self.inst.chunk_size = 1024000

    def load_config(self, file_path):
        with open(file_path, 'r') as config_file:
            return json.load(config_file)
    config = load_config(file_path)
        

    def send_to_2182A(self, command):
        self.inst.write(f'SYST:COMM:SER:SEND "{command}"')
        time.sleep(0.1)  # Allow time for command execution

    def query_2182A(self, command):
        self.send_to_2182A(self, command)
        time.sleep(0.1)  # Allow time for command execution
        self.inst.write('SYST:COMM:SER:ENT?')
        time.sleep(0.1)  # Allow time for response
        return self.inst.read().strip()

    def initialize_and_setup_instrument(self, config):
        inst = self.inst.open_resource(config['address'])
        inst.timeout = 20000  # 20 second timeout
    
        # Initialize and setup the 6221
        for command in config['init_commands'] + config['setup_commands']:
            inst.write(command['cmd'])
            time.sleep(0.1)  # Small delay between commands
    
        # Setup the 2182A through the 6221
        for command in config['2182A_commands']:
            self.send_to_2182A(inst, command['cmd'])
            time.sleep(0.2)  # Slightly longer delay for 2182A commands
    
        return inst

    def compare_values(self, expected, actual, tolerance=1e-9):
        try:
            expected_float = float(expected)
            actual_float = float(actual)
            return np.isclose(expected_float, actual_float, rtol=tolerance, atol=tolerance)
        except ValueError:
            return expected == actual

    def verify_instrument_setup(self, inst, config):
        all_verified = True

        # Verify 6221 setup
        for query in config['query_commands']:
            response = inst.query(query['cmd']).strip()
            if not self.compare_values(query['expected'], response):
                print(f"Warning: 6221 Query '{query['cmd']}' did not return expected value.")
                print(f"Expected: {query['expected']}, Got: {response}")
                all_verified = False

        # Verify 2182A setup
        for query in config['2182A_query_commands']:
            response = self.query_2182A(query['cmd'])
            if not self.compare_values(query['expected'], response):
                print(f"Warning: 2182A Query '{query['cmd']}' did not return expected value.")
                print(f"Expected: {query['expected']}, Got: {response}")
                all_verified = False

        if all_verified:
            print("All queried settings verified successfully for 6221 and 2182A")
        else:
            print("Some settings could not be verified. Please check the warnings above.")

    def close(self):
        self.inst.close()
        self.rm.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    