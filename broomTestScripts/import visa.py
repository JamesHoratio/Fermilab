#import pyvisa
#
## Check available backends
#print("Available backends:", pyvisa.highlevel.list_backends())
#
## Initialize the resource manager with the appropriate backend
#rm = pyvisa.ResourceManager('@py')  # Use '@ni' if using NI-VISA, adjust if using a different backend
#
#try:
#    resourceinfo = rm.list_resources()
#    print(resourceinfo)
#except pyvisa.errors.VisaIOError as e:
#    print(f"VISA error: {e}")
#except Exception as e:
#    print(f"Unexpected error: {e}")
#
#import pyvisa
#import time
#
## Constants
#INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"  # Change this to your instrument's resource string
#INSTRUMENT_RESOURCE_STRING_2182A = "ASRL1::INSTR"  # COM2 port
#
#def main():
#    try:
#        # Initialize the resource manager
#        rm = pyvisa.ResourceManager('@py')
#
#        # Connect to the 6221 via TCP/IP
#        k6221 = rm.open_resource(INSTRUMENT_RESOURCE_STRING_6221)
#        
#        # Set termination characters for 6221
#        k6221.write_termination = '\n'
#        k6221.read_termination = '\n'
#        
#        # Query the instrument identification for 6221
#        connectmessage_6221 = k6221.query('*IDN?')
#        print("Connected 6221 Instrument ID:", connectmessage_6221)
#
#        # Configure the serial port settings for 2182A through the 6221
#        k2182A = rm.open_resource(INSTRUMENT_RESOURCE_STRING_2182A)
#        k2182A.baud_rate = 19200
#        k2182A.data_bits = 8
#        k2182A.parity = pyvisa.constants.Parity.none
#        k2182A.stop_bits = pyvisa.constants.StopBits.one
#        k2182A.flow_control = pyvisa.constants.ControlFlow.none
#
#        # Set termination characters for 2182A
#        k2182A.write_termination = '\n'
#        k2182A.read_termination = '\n'
#
#        # Send configuration commands to 6221 to communicate with 2182A
#        k6221.write('SYST:COMM:SER:SEND "*IDN?"')
#        time.sleep(1)
#        response_2182A = k6221.query('SYST:COMM:SER:ENT?')
#        print("Connected 2182A Instrument ID:", response_2182A)
#
#        # Close the resources
#        k6221.close()
#        k2182A.close()
#        rm.close()
#
#    except pyvisa.VisaIOError as e:
#        print(f"VISA error: {e}")
#    except Exception as e:
#        print(f"Unexpected error: {e}")
#
#if __name__ == "__main__":
#    main()

import pyvisa
import time

# Constants
INSTRUMENT_RESOURCE_STRING_6221 = "TCPIP0::169.254.47.133::1394::SOCKET"  # Change this to your instrument's resource string
INSTRUMENT_RESOURCE_STRING_2182A = "ASRL3::INSTR"  # Update this to the correct COM port

def main():
    try:
        # Initialize the resource manager
        rm = pyvisa.ResourceManager()

        # Connect to the 6221 via TCP/IP
        k6221 = rm.open_resource(INSTRUMENT_RESOURCE_STRING_6221)
        k6221.write_termination = '\n'
        k6221.read_termination = '\n'

        # Query the instrument identification for 6221
        connectmessage_6221 = k6221.query('*IDN?')
        print("Connected 6221 Instrument ID:", connectmessage_6221)

        # Configure the serial port settings for 2182A through the 6221
        k6221.write('SYST:COMM:SER:BAUD 19200')
        k6221.write('SYST:COMM:SER:DATA 8')
        k6221.write('SYST:COMM:SER:PAR NONE')
        k6221.write('SYST:COMM:SER:STOP 1')
        k6221.write('SYST:COMM:SER:FLOW NONE')

        # Send a command to the 2182A through the 6221's serial port
        k6221.write('SYST:COMM:SER:SEND "*IDN?"')

        # Read the response from the 2182A
        response_2182A = k6221.query('SYST:COMM:SER:ENT?')
        print("Connected 2182A Instrument ID:", response_2182A)

        # Close the resources
        k6221.close()
        rm.close()

    except pyvisa.VisaIOError as e:
        print(f"VISA error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
