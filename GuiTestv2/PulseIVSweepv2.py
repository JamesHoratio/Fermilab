"""Keithley PyVisa example code that connects to 6221 + 2182/2182A instrument
stack and runs delta measurements with user parameters from GUI.

Set INSTRUMENT_RESOURCE_STRING equal to your instrument's resource string, found using the
    VISA Interactive Control program.

Note: 6221 Buffer can only store a max of 65,536 readings, limiting the amount of data this
program can collect.

    Copyright 2023 Tektronix, Inc.                      
    See www.tek.com/sample-license for licensing terms.
"""
import os
import time
import datetime
import textwrap
from instrcomms import Communications
from instrgui import InstrumentOption, open_gui_return_input

DEBUG_PRINT_COMMANDS = True

# Ensure the parameters file is in the current working directory
SAVED_PARAMETERS_FILENAME = os.path.join(os.getcwd(), "sweep_parameters.txt")

def experiment_setup(instrument, parameters, start_time):
    """Set up instrument parameters for linear sweep test"""
    filter_type = int(parameters["filter_type"])
    filter_count = int(parameters["filter_count"])
    integration_nplcs = float(parameters["integration_NPLCs"])
    volt_compliance = float(parameters["volt_compliance"])
    guarding_on = parameters["guarding_on"]
    low_to_earth_on = parameters["lowToEarth_on"]
    sweepdelay = float(parameters["sweepdelay"])
    pulsehighcurrent = float(parameters["pulsehighcurrent"])
    pulselowcurrent = float(parameters["pulselowcurrent"])
    pulsecount = int(parameters["pulsecount"])
    pulsesweeprange = parameters["pulsesweeprange"]
    pulsewidth = float(parameters["pulsewidth"])
    pulsedelay = float(parameters["pulsedelay"])
    pulsesweepstate = int(parameters["pulsesweepstate"])
    pulselowmeas = int(parameters["pulselowmeas"])
    pulseinterval = float(parameters["pulseinterval"])
    pulsecompliance = float(parameters["pulsecompliance"])
    pulsesweepspacing = parameters["pulsesweepspacing"]
    pulsesweepstart = float(parameters["pulsesweepstart"])
    pulsesweepstop = float(parameters["pulsesweepstop"])
    pulsesweepstep = float(parameters["pulsesweepstep"])
    pulsevoltagerange = float(parameters["pulsevoltagerange"])
    pulsefilterstate = int(parameters["pulsefilterstate"])
    #pulsefiltercount = int(parameters["pulsefiltercount"])
    #pulsefiltertype = int(parameters["pulsefiltertype"])
    #num_readings = pulsecount + (pulsecount * pulselowmeas)
    
    query2182Apresent = int(instrument.query("sour:pdel:nvpresent?"))
    if query2182Apresent == 0:
        print("2182A not present")
        instrument.disconnect()
        stop_time = time.time()  # Stop the timer...
        print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")
        exit()

    invalid_parameters = False
    if pulsehighcurrent == pulselowcurrent:
        print("High and low current cannot be the same")
        invalid_parameters = True
    if pulsecount < 1 or pulsecount > 65536:
        print("Number of readings must be in range [1, 65536]")
        invalid_parameters = True
    if filter_type not in [0, 1, 2]:
        print("Filter type must be 0, 1, or 2")
        invalid_parameters = True
    if (filter_count < 2 or filter_count > 300) and filter_type != 0:
        print("If filter is enabled, filter count must be in range [2, 300]")
        invalid_parameters = True
    if pulsedelay < 1e-3 or pulsedelay > 9999.999:
        print("Delay must be in range [1e-3, 9999.999]")
        invalid_parameters = True
    if volt_compliance < 0.1 or volt_compliance > 105:
        print("Voltage compliance must be in range [0.1, 105]")
        invalid_parameters = True

    if invalid_parameters:
        instrument.disconnect()
        stop_time = time.time()  # Stop the timer...
        print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")
        exit()

    # Abort tests in the other modes
    instrument.write("SOUR:SWE:ABOR")
    instrument.write("SOUR:WAVE:ABOR")

    instrument.write("*RST")  # Reset the 6221
    time.sleep(2) # Wait 2 seconds
    instrument.write("SYST:COMM:SERIAL:SEND \"*RST\"")  # Reset the 2182A
    time.sleep(3) # Wait 3 seconds
    # Use Guard?
    if guarding_on:
        instrument.write("OUTP:ISH GUARD")
    else:
        instrument.write("OUTP:ISH OLOW")

    # Low to Earth?
    if low_to_earth_on:
        instrument.write("OUTP:LTE ON")
    else:
        instrument.write("OUTP:LTE OFF")

    time.sleep(0.5)

    sweepdelay = ((pulsecount * 1/50 - 6)/1000)
    
    instrument.write(f"SOUR:DEL {sweepdelay}") # Set delay between pulses
    instrument.write("form:elem READ,TST,RNUM,SOUR")  # Set readings to be returned
    instrument.write(f"SOUR:CURR:COMP {volt_compliance}")  # Set voltage compliance
    instrument.write(f"sour:pdel:high {pulsehighcurrent}")  # Set high current
    instrument.write(f"sour:pdel:low {pulselowcurrent}")  # Set low current
    instrument.write(f"sour:pdel:count {pulsecount}")  # Set num readings
    instrument.write(f"sour:pdel:rang best")  # Best uses lowest range which will handle all sweep steps
    instrument.write(f"sour:swe:rang {pulsesweeprange}")  # Set sweep range
    instrument.write(f"sour:pdel:width {pulsewidth}")  # Set pulse width
    instrument.write(f"sour:pdel:sdel {pulsedelay}")  # Set pulse delay
    instrument.write(f"sour:pdel:swe {pulsesweepstate}")  # Set pulse sweep state
    instrument.write(f"sour:pdel:lme {pulselowmeas}")  # Set # of low measurements
    instrument.write(f"sour:pdel:int {pulseinterval}")  # Set pulse interval
    instrument.write(f"sour:curr:comp {pulsecompliance}")  # Set pulse compliance
    instrument.write(f"sour:swe:spac {pulsesweepspacing}")  # Set pulse sweep spacing
    instrument.write(f"sour:curr:start {pulsesweepstart}")  # Set pulse sweep start
    instrument.write(f"sour:curr:stop {pulsesweepstop}")  # Set pulse sweep stop
    instrument.write(f"sour:curr:step {pulsesweepstep}")  # Set pulse sweep step
    instrument.write(f"SYST:COMM:SERIAL:SEND \":sens:volt:rang {pulsevoltagerange}\"")  # Set voltage measure range
    instrument.write(f"sens:aver:wind 0")  # Set averaging window
    instrument.write(f"sens:aver:stat {pulsefilterstate}")  # Set filter state
    #instrument.write(f"sens:aver:count {pulsefiltercount}")  # Set filter count
    #instrument.write(f"sens:aver:tcon {pulsefiltertype}")  # Set filter type
    instrument.write(f"SYST:COMM:SERIAL:SEND \":SENS:VOLT:NPLC {integration_nplcs}\"")  # Set NPLC for 2182A
    time.sleep(0.5)

    # Set the filter type
    if filter_type == 0:
        instrument.write("SENS:AVER:TCON MOV")
        instrument.write("SENS:AVER:STAT 0")  # turn off filter
    elif filter_type == 1:
        instrument.write("SENS:AVER:TCON MOV")
        instrument.write(f"SENS:AVER:COUNT {filter_count}")  # set filter count
        instrument.write("SENS:AVER:STAT 1")  # turn on filter
    elif filter_type == 2:
        instrument.write("SENS:AVER:TCON REP")
        instrument.write(f"SENS:AVER:COUNT {filter_count}")  # set filter count
        instrument.write("SENS:AVER:STAT 1")  # turn on filter
    else:
        print("Error: Invalid filter type parameter")
        exit()
    time.sleep(2)
    instrument.write("UNIT V")  # Set units (other options are OHMS, W, SIEM)

def read_data(instrument, num_readings: int):
    """Wait for instruments to finish measuring and read data"""
    # Wait for sweep to finish
    sweep_done = False
    data = []
    while not sweep_done:
        time.sleep(1)
        oper_byte_status = instrument.query(
            "STAT:OPER:EVEN?"
        )  # Check the event register
        oper_byte_status = int(oper_byte_status)  # Convert decimal string to int
        sweep_done = oper_byte_status & (1 << 1)  # bit mask to check if sweep done

    # Get the measurements 1000 at a time
    for i in range((num_readings - 1) // 1000 + 1):
        if num_readings - i * 1000 > 1000:  # if more than 1000 readings left
            data_sel_count = 1000
        else:
            data_sel_count = num_readings - i * 1000

        # Transfer readings over GPIB
        raw_data = instrument.query(f"TRAC:DATA:SEL? {i * 1000},{data_sel_count}")
        raw_data = raw_data.split(",")
        data.extend(raw_data)

    return data

def write_csv(data, csv_path: str):
    """Write data to csv file"""
    # Create and open file
    with open(csv_path, "a+", encoding="utf-8") as csv_file:
        # Write the measurements to the CSV file
        csv_file.write(
            "Voltage Reading, Timestamp, Source Current, Reading Number, Resistance\n"
        )

        # We queried 4 values per reading, so iterate over groups of 4 elements
        for i in range(0, len(data), 4):
            v_reading = data[i]
            time_stamp = data[i + 1]
            source_current = data[i + 2]
            reading_number = data[i + 3]
            resistance = float(v_reading) / float(source_current)
            csv_file.write(
                f"{v_reading}, {time_stamp}, {source_current}, {reading_number}, {resistance}\n"
            )
            csv_file.flush()

def main():
    """Main function. Connect to instrument, get test params through GUI, run test, save data."""
    start_time = time.time()  # Start the timer...
    inst_6221 = Communications("GPIB0::12::INSTR")
    inst_6221.connect()

    # Options to be displayed in GUI
    instrument_options = [
        InstrumentOption(
            "Pulse High Current",
            "pulsehighcurrent",
            "0.001",
            tooltip="Sets high pulse value (amps). [-105e-3 to 105e-3]",
        ),
        InstrumentOption(
            "Pulse Low Current",
            "pulselowcurrent",
            "0",
            tooltip="Sets low pulse value (amps). [-105e-3 to 105e-3]",
        ),
        InstrumentOption(
            "Pulse Sweep Spacing",
            "pulsesweepspacing",
            "LIN",
            tooltip="LIN = Linear, LOG = Logarithmic",
        ),
        InstrumentOption(
            "Pulse Sweep Start",
            "pulsesweepstart",
            "0.001",
            tooltip="Initial value of the pulse sweep",
        ),
        InstrumentOption(
            "Pulse Sweep Stop",
            "pulsesweepstop",
            "0.01",
            tooltip="Final value of the pulse sweep",
        ),
        InstrumentOption(
            "Pulse Sweep Step",
            "pulsesweepstep",
            "0.001",
        ),
        InstrumentOption(
            "Number of Pulses",
            "pulsecount",
            "11",
            tooltip="Number of pulses in the sweep including the start and stop values",
        ),
        InstrumentOption(
            "Pulse Sweep Range",
            "pulsesweeprange",
            "best",
            tooltip="Best or Auto range for the pulse sweep",
        ),
        InstrumentOption(
            "Pulse Width",
            "pulsewidth",
            "0.001",
            tooltip="Width of the pulse",
        ),
        InstrumentOption(
            "Pulse Sweep State",
            "pulsesweepstate",
            "0",
            tooltip="0 = Off, 1 = On",
        ),
        InstrumentOption(
            "Pulse Low Measurement",
            "pulselowmeas",
            "0",
            tooltip="Set number of low measurements. NRf = 1 or 2",
        ),
        InstrumentOption(
            "Pulse Interval (sec)",
            "pulseinterval",
            "0.5",
            tooltip="Interval between pulses (pulse duty cycle = pulse / (interval between pulses + pulse width))",
        ),
        InstrumentOption(
            "Pulse Compliance",
            "pulsecompliance",
            "10",
            tooltip="Voltage compliance must be in range [0.1, 105]",
        ),
        InstrumentOption(
            "Pulse Delay",
            "pulsedelay",
            "0.5",
            tooltip="Pulse settle time delay between current source change and measurement trigger.",
        ),
        InstrumentOption(
            "Filter Type",
            "filter_type",
            tooltip="0 = No Filter, 1 = Moving Filter, 2 = Repeat Filter",
        ),
        InstrumentOption(
            "Filter Count",
            "filter_count",
            "2",
            tooltip="Must be in range [2, 300] if filter in use",
        ),
        InstrumentOption(
            "Pulse Filter State",
            "pulsefilterstate",
            "0",
            tooltip="0 = Off, 1 = On",
        ),
        InstrumentOption(
            "Pulse Voltage Range",
            "pulsevoltagerange",
            "0.1",
            tooltip="Valid Voltage Ranges: 0.01, 0.1, 1, 10 or 100",
        ),
        InstrumentOption(
            "Sweep Delay",
            "sweepdelay",
            "0.5",
            tooltip="Delay between sweeps in seconds",
        ),

        InstrumentOption("Integration NPLCs", "integration_NPLCs", "5"),
        InstrumentOption(
            "Voltage Compliance",
            "volt_compliance",
            "10",
            tooltip="Voltage compliance must be in range [0.1, 105]",
        ),
        InstrumentOption("Use Guard", "guarding_on", False, True),
        InstrumentOption("Use Low to Earth", "lowToEarth_on", False, True),
    ]

    messages = (
        "Test Setup: Connect the 6221 Current Source and 2182 Nanovoltmeter "
        "through their RS-232 ports and connect the 6221 to this PC via GPIB adapter."
    )

    # Wrap messages so each line is no more than 40 characters.
    messages = "\n".join(textwrap.wrap(messages, 40))

    parameters = open_gui_return_input(
        instrument_options, messages, SAVED_PARAMETERS_FILENAME
    )

    # If user clicks close button on app window without clicking run
    if list(parameters.values())[0] is None:
        print("Application window closed without starting test; aborting")
        inst_6221.disconnect()
        stop_time = time.time()  # Stop the timer...

        print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")
        exit()

    pulsecount = int(parameters["pulsecount"])
    pulselowmeas = int(parameters["pulselowmeas"])
    num_readings = pulsecount + (pulsecount * pulselowmeas)
    
    experiment_setup(inst_6221, parameters, start_time)

    inst_6221.write("sour:pdel:arm")  # Arm the test
    time.sleep(3)
    inst_6221.write("init:imm")  # Start the test

    data = read_data(inst_6221, num_readings)

    date = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    csv_path = f".\\PulsedIVLinear_Measurements {date}.csv"
    write_csv(data, csv_path)

    inst_6221.write(
        ":SOUR:SWE:ABORT"
    )  # Abort the test to prevent the output being left on

    inst_6221.disconnect()

    stop_time = time.time()  # Stop the timer...

    # Notify the user of completion and the data streaming rate achieved.
    print("done")
    print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")

    exit()

if __name__ == "__main__":
    main()
