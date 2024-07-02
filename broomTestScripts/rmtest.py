#import pyvisa as visa
#K6221Address = ""
#rm = pyvisa.ResourceManager()
#rm = visa.ResourceManager()
#k6 = rm.open_resource(K6221Address, write_termination='\n', read_termination='\n')
#print(rm)
#devlist = rm.list_resources()
#print(devlist)  # device list feedback is ('ASRL7::INSTR', 'ASRL8::INSTR', 'ASRL9::INSTR')
###RS232 = rm.open_resource('ASRL9::INSTR')
### You may need to configure further the resource by setting explicitly the
### baud rate, parity, termination character, etc before being able to communicate
### Those depend on your instrument.
###RS232.write("V")
###print(RS232.read())
#import pyvisa
#
#def identify_resources(resource_strings):
#    try:
#        # Initialize the resource manager
#        rm = pyvisa.ResourceManager()
#
#        # Iterate through the specified resource strings and query their identification
#        for resource in resource_strings:
#            try:
#                inst = rm.open_resource(resource)
#                inst.write_termination = '\n'
#                inst.read_termination = '\n'
#                idn_response = inst.query('*IDN?')
#                print(f"Resource: {resource}, IDN: {idn_response}")
#                inst.close()
#            except pyvisa.VisaIOError as e:
#                print(f"Could not access resource {resource}: {e}")
#            except Exception as e:
#                print(f"Unexpected error with resource {resource}: {e}")
#
#        rm.close()
#
#    except pyvisa.VisaIOError as e:
#        print(f"VISA error: {e}")
#    except Exception as e:
#        print(f"Unexpected error: {e}")
#
#if __name__ == "__main__":
#    # Specify a list of common resource strings to check
#    resource_strings = [
#        "TCPIP0::169.254.47.133::1394::SOCKET",  # Example for 6221 via TCP/IP
#        "ASRL1::INSTR",  # Example for serial COM1
#        "ASRL2::INSTR",  # Example for serial COM2
#        "ASRL3::INSTR"   # Example for serial COM3
#    ]
#    
#    identify_resources(resource_strings)
#
#import pyvisa
#import serial.tools.list_ports
#
#def list_serial_ports():
#    ports = serial.tools.list_ports.comports()
#    return [port.device for port in ports]
#
#def identify_resources(resource_strings):
#    try:
#        # Initialize the resource manager
#        rm = pyvisa.ResourceManager()
#
#        # Iterate through the specified resource strings and query their identification
#        for resource in resource_strings:
#            try:
#                inst = rm.open_resource(resource)
#                inst.write_termination = '\n'
#                inst.read_termination = '\n'
#                idn_response = inst.query('*IDN?')
#                print(f"Resource: {resource}, IDN: {idn_response}")
#                inst.close()
#            except pyvisa.VisaIOError as e:
#                print(f"Could not access resource {resource}: {e}")
#            except Exception as e:
#                print(f"Unexpected error with resource {resource}: {e}")
#
#        rm.close()
#
#    except pyvisa.VisaIOError as e:
#        print(f"VISA error: {e}")
#    except Exception as e:
#        print(f"Unexpected error: {e}")
#
#if __name__ == "__main__":
#    # Dynamically list available serial ports
#    serial_ports = list_serial_ports()
#    print(f"Available serial ports: {serial_ports}")
#
#    # Create resource strings for available serial ports
#    resource_strings = [
#        "TCPIP0::169.254.47.133::1394::SOCKET",  # Example for 6221 via TCP/IP
#    ] + [f"ASRL{port[-1]}::INSTR" for port in serial_ports]
#    
#    identify_resources(resource_strings)
#
#import pyvisa
#
#def identify_resources(resource_strings):
#    try:
#        # Initialize the resource manager
#        rm = pyvisa.ResourceManager()
#
#        # Iterate through the specified resource strings and query their identification
#        for resource in resource_strings:
#            try:
#                inst = rm.open_resource(resource)
#                inst.write_termination = '\n'
#                inst.read_termination = '\n'
#                idn_response = inst.query('*IDN?')
#                print(f"Resource: {resource}, IDN: {idn_response}")
#                inst.close()
#            except pyvisa.VisaIOError as e:
#                print(f"Could not access resource {resource}: {e}")
#            except Exception as e:
#                print(f"Unexpected error with resource {resource}: {e}")
#
#        rm.close()
#
#    except pyvisa.VisaIOError as e:
#        print(f"VISA error: {e}")
#    except Exception as e:
#        print(f"Unexpected error: {e}")
#
#if __name__ == "__main__":
#    # Specify known resource strings to check
#    resource_strings = [
#        "TCPIP0::169.254.47.133::1394::SOCKET",  # Example for 6221 via TCP/IP
#        "ASRL1::INSTR",  # Example for serial COM1
#        "ASRL2::INSTR",  # Example for serial COM2
#        "ASRL3::INSTR",  # Example for serial COM3
#        "ASRL4::INSTR",  # Try additional COM ports if necessary
#        "ASRL5::INSTR"
#    ]
#    
#    identify_resources(resource_strings)
#import serial.tools.list_ports
#
#def list_serial_ports():
#    ports = serial.tools.list_ports.comports()
#    for port in ports:
#        print(f"Port: {port.device}, Description: {port.description}, HWID: {port.hwid}")
#
#if __name__ == "__main__":
#    print("Available serial ports:")
#    list_serial_ports()
#
#import pyvisa as visa
#import time
#
## Define the resource string for the 6221
#INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"
#SLEEP_INTERVAL = 0.1
#
#class Test2182ARead:
#    def __init__(self):
#        self.rm = visa.ResourceManager('@ivi')
#        self.k6221 = self.rm.open_resource(INSTRUMENT_RESOURCE_STRING_6221)
#        self.k6221.write_termination = '\n'
#        self.k6221.read_termination = '\n'
#        self.k6221.timeout = 60000
#
#
#    def send_command(self, command):
#        self.k6221.write(command)
#
#    def send_command_to_2182A(self, command):
#        self.send_command(f'SYST:COMM:SER:SEND "{command}"')
#
#    def query_command(self, command):
#        return self.k6221.query(command)
#
#    def query_command_to_2182A(self, command):
#        self.send_command_to_2182A(command)
#        return self.query_command('SYST:COMM:SER:ENT?').strip()
#
#    def fetch_existing_data1(self):
#        voltages = self.query_command_to_2182A('trac:data?').strip().strip('[]')
#        return [float(v) for v in voltages.split(',')]
#    
#    def fetch_existing_data(self):
#        voltages = self.query_command_to_2182A('trac:data?').strip().strip('[]')
#        return [float(v) for v in voltages.split(',')]
#    
#    def fetch_data(self):
#        #data = []
#        raw_data = self.query_command_to_2182A('trac:data?').strip().strip('[]')
#        data.extend(raw_data.split(","))
#        return [float(i) for i in data]
#    
#    def fetch_data_6221(self):
#        data = []
#        raw_data = self.query_command('trac:data?').strip()
#        return [float(v) for v in raw_data.split(",")]
#
#if __name__ == "__main__":
#    test = Test2182ARead()
#    #voltages = []
#    voltages = test.fetch_existing_data()
#    for i, voltage in enumerate(voltages):
#        print(f"Stored Measurement {i+1}: {voltage} V")
#    
#    data = test.fetch_data_6221()
#    for p, data in enumerate(data):
#        print(f"6221 Stored Measurement {p+1}: {voltage}")
#
import pyvisa as visa
import time

# Define the resource string for the 6221
INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"
SLEEP_INTERVAL = 0.1

class Test2182ARead:
    def __init__(self):
        self.rm = visa.ResourceManager('@ivi')
        self.k6221 = self.rm.open_resource(INSTRUMENT_RESOURCE_STRING_6221)
        self.k6221.write_termination = '\n'
        self.k6221.read_termination = '\n'
        self.k6221.timeout = 60000

    def send_command(self, command):
        self.k6221.write(command)

    def send_command_to_2182A(self, command):
        self.send_command(f'SYST:COMM:SER:SEND "{command}"')

    def query_command(self, command):
        return self.k6221.query(command)

    def query_command_to_2182A(self, command):
        self.send_command_to_2182A(command)
        return self.query_command('SYST:COMM:SER:ENT?').strip()

    def fetch_existing_data(self):
        voltages = self.query_command_to_2182A('trac:data?').strip().strip('[]')
        return [float(v) for v in voltages.split(',')]

    def fetch_data(self):
        raw_data = self.query_command_to_2182A('trac:data?').strip().strip('[]')
        data = raw_data.split(',')
        return [float(i) for i in data if i]  # Only convert non-empty strings to float

    def fetch_data_6221(self):
        raw_data = self.query_command('trac:data?').strip()
        data = raw_data.split(',')
        return [float(v) for v in data if v]  # Only convert non-empty strings to float

if __name__ == "__main__":
    test = Test2182ARead()
    voltages = test.fetch_existing_data()
    for i, voltage in enumerate(voltages):
        print(f"Stored Measurement {i+1}: {voltage} V")
    
    try:
        data_6221 = test.fetch_data_6221()
        for p, value in enumerate(data_6221):
            print(f"6221 Stored Measurement {p+1}: {value}")
    except ValueError as e:
        print(f"Error reading 6221 data: {e}")
