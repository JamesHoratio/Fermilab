# config.py

# Instrument settings
INSTRUMENT_ADDRESS = "TCPIP0::169.254.47.133::1394::SOCKET"
TIMEOUT = 20000  # 20 seconds timeout

# Default sweep parameters
DEFAULT_START_LEVEL = 0
DEFAULT_STOP_LEVEL = 10e-3
DEFAULT_NUM_PULSES = 11
DEFAULT_SWEEP_TYPE = 'LIN'

# Voltage measure range options
VOLTAGE_RANGES = ['100 mV', '1 V', '10 V', '100 V']
DEFAULT_VOLTAGE_RANGE = '100 mV'

# Graph settings
GRAPH_TITLE = "Pulsed IV Graph"
X_AXIS_LABEL = "Current (A)"
Y_AXIS_LABEL = "Voltage (V)"