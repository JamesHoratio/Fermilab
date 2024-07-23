#import pyvisa as visa
#.instrumentAddress = ""
#rm = pyvisa.ResourceManager()
#rm = visa.ResourceManager()
#k6 = rm.open_resource.instrumentAddress, write_termination='\n', read_termination='\n')
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
#        self.instrument = self.rm.open_resource(INSTRUMENT_RESOURCE_STRING_6221)
#        self.instrument.write_termination = '\n'
#        self.instrument.read_termination = '\n'
#        self.instrument.timeout = 60000
#
#
#    def send_command(self, command):
#        self.instrument.write(command)
#
#    def send_command_to_2182A(self, command):
#        self.send_command(f'SYST:COMM:SER:SEND "{command}"')
#
#    def query_command(self, command):
#        return self.instrument.query(command)
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
        self.instrument = self.rm.open_resource(INSTRUMENT_RESOURCE_STRING_6221)
        self.instrument.write_termination = '\n'
        self.instrument.read_termination = '\n'
        self.instrument.timeout = 60000

    def send_command(self, command):
        self.instrument.write(command)

    def send_command_to_2182A(self, command):
        self.send_command(f'SYST:COMM:SER:SEND "{command}"')

    def query_command(self, command):
        return self.instrument.query(command)

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

    def testEnter(self):
        self.instrument.write('SYST:COMM:SERIal:SEND "*RST"') # reset the 2182A
        time.sleep(2)
        self.instrument.write('SYST:COMM:SERIal:SEND "SYST:FFIL ON"') # turn on the fast filter
        time.sleep(2)
        time.sleep(0.2)
        print("Reset")
        #self.instrument.write('SYST:COMM:SERIal:SEND "trac:data?"')
        self.instrument.write(':SYST:COMM:SERIal:SEND ":sens:volt:rang 10"') # set 2182A to 10mV range for best sensitivity on the 5mV expected signal
        time.sleep(0.4)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":sens:volt:nplc 0.1"') # set 2182A to 0.01 NPLC for faster measurements
        time.sleep(0.4)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:cle"') # clear the buffer
        time.sleep(0.4)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:feed sens"') # 
        time.sleep(0.2)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:poin 11"') # 
        time.sleep(0.2)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trig:sour ext"') # 
        time.sleep(0.4)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trig:coun 11"') # 
        time.sleep(0.4)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":trac:feed:control next"') # 
        time.sleep(0.5)
        self.instrument.write(':SYST:COMM:SERIal:SEND ":sens:volt:rang?"')
        time.sleep(1)
        data = self.instrument.query('SYST:COMM:SERIal:ENT?')
        time.sleep(0.2)
        data2 = self.instrument.query('SYST:COMM:SERIal:ENT?')
        time.sleep(2)
        data3 = self.instrument.query('SYST:COMM:SERIal:ENT?')
        time.sleep(0.1)
        data4 = self.instrument.query('SYST:COMM:SERIal:ENT?')
        #enter = self.instrument.query('ENTER255')
        print(f"Data: {data}")
        print(f"Data2: {data2}")
        print(f"Data3: {data3}")
        print(f"Data4: {data4}")
        #print(f"Enter: {enter}")

    def testenter2(self):
        #self.instrument.write('SYST:COMM:SERIal:SEND "syst:key 17"') # reset the 2182A
        #time.sleep(2)
        self.instrument.write(':SYST:COMM:SERIal:SEND "trac:data?"')
        time.sleep(1)
        data = self.instrument.query('SYST:COMM:SERIal:ENT?')
        time.sleep(0.2)
        data2 = self.instrument.query('SYST:COMM:SERIal:ENT?')
        time.sleep(2)
        data3 = self.instrument.query('SYST:COMM:SERIal:ENT?')
        time.sleep(0.1)
        data4 = self.instrument.query('SYST:COMM:SERIal:ENT?')
        #enter = self.instrument.query('ENTER255')
        print(f"Data: {data}")
        print(f"Data2: {data2}")
        print(f"Data3: {data3}")
        print(f"Data4: {data4}")
#
        #elementFormat = self.instrument.query('form:elem?')
        #time.sleep(0.2)
        #print(f"Element Format: {elementFormat}")
        time.sleep(2)
        k6221data = self.instrument.query('trac:data?')
        #k6221data = k6221data.split(',')
        #for i, value in enumerate(k6221data):
        #    print(f"Data 6221 #{i+1}: {value}")
        print(f"Data 6221 #1: {k6221data}")

    
if __name__ == "__main__":
    test = Test2182ARead()
    #voltages = test.fetch_existing_data()
    #for i, voltage in enumerate(voltages):
    #    print(f"Stored Measurement {i+1}: {voltage} V")
    #
    #try:
    #    data_6221 = test.fetch_data_6221()
    #    for p, value in enumerate(data_6221):
    #        print(f"6221 Stored Measurement {p+1}: {value}")
    #except ValueError as e:
    #    print(f"Error reading 6221 data: {e}")
    test.testenter2()
    k6221data = test.fetch_data_6221()
    print(f"6221 Data: {k6221data}")

