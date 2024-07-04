# config.py

# Instrument settings
INSTRUMENT_ADDRESS = "TCPIP0::169.254.47.133::1394::SOCKET"
TIMEOUT = 20000  # 20 seconds timeout

# Default sweep parameters
DEFAULT_START_LEVEL = 0  # Amps
DEFAULT_STOP_LEVEL = 10e-3  # 10 mA
DEFAULT_NUM_PULSES = 11
DEFAULT_SWEEP_TYPE = 'LIN'  # 'LIN' for linear, 'LOG' for logarithmic

# Voltage measure range options
VOLTAGE_RANGES = ['100 mV', '1 V', '10 V', '100 V']
DEFAULT_VOLTAGE_RANGE = '100 mV'

# Default pulse settings
DEFAULT_PULSE_WIDTH = '500e-6'  # 500 µs
DEFAULT_PULSE_DELAY = '1e-3'  # 1 ms
DEFAULT_PULSE_INTERVAL = '5'  # 5 PLC (Power Line Cycles)

# Buffer settings
DEFAULT_BUFFER_SIZE = 5000

# Compliance settings
DEFAULT_CURRENT_COMPLIANCE = '100E-3'  # 100 mA

# Graph settings
GRAPH_TITLE = "Pulsed IV Graph"
X_AXIS_LABEL = "Current (A)"
Y_AXIS_LABEL = "Voltage (V)"

# GUI settings
GUI_WINDOW_SIZE = "1000x600"
GUI_TITLE = "Broom - Pulsed IV Measurements"

# File settings
DEFAULT_FILE_PREFIX = "PulsedIV_"
DEFAULT_FILE_EXTENSION = ".csv"

# Delay settings
SETUP_DELAY = 0.35  # 350 ms delay between setup commands
DATA_PROCESSING_DELAY = 5  # 5 seconds delay for data processing

# Error messages
CONNECTION_ERROR = "Failed to connect to the instrument."
MEASUREMENT_ERROR = "An error occurred during measurement: {}"
DISCONNECTION_MESSAGE = "Disconnected from the instrument."
CONNECTION_SUCCESS = "Successfully connected to the instrument."
MEASUREMENT_COMPLETE = "Pulsed IV sweep completed successfully."

# Other constants
PLC_60HZ = 1/60  # Duration of one Power Line Cycle for 60 Hz
PLC_50HZ = 1/50  # Duration of one Power Line Cycle for 50 Hz