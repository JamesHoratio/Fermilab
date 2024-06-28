"""Keithley PyVisa example code that connects to 6221 + 2182/2182A instrument
stack and runs delta measurements with user parameters from GUI.

Set INSTRUMENT_RESOURCE_STRING equal to your instrument's resource string, found using the
    VISA Interactive Control program.

Note: 6221 Buffer can only store a max of 65,536 readings, limiting the amount of data this
program can collect.

    Copyright 2023 Tektronix, Inc.                      
    See www.tek.com/sample-license for licensing terms.
"""
import sys
import os
import csv
import struct
import time
import datetime
import textwrap
import pyvisa as visa
from instrcomms import Communications
from instrgui import InstrumentOption, open_gui_return_input

DEBUG_PRINT_COMMANDS = True

INSTRUMENT_RESOURCE_STRING = "GPIB0::12::INSTR"  # Change this to your instrument's resource string

SAVED_PARAMETERS_FILENAME = ("sweep_parameters.txt")

def experiment_setup(instrument, parameters, start_time):
    """Set up instrument parameters for linear sweep test"""
    volt_compliance = float(parameters["volt_compliance"])
    guarding_on = parameters["guarding_on"]
    low_to_earth_on = parameters["lowToEarth_on"]
    pulsecount = int(parameters["pulsecount"])
    pulsedelay = float(parameters["pulsedelay"])
    pulselowmeas = int(parameters["pulselowmeas"])
    pulsecompliance = float(parameters["pulsecompliance"])
    pulsesweepstart = float(parameters["pulsesweepstart"])
    pulsesweepstop = float(parameters["pulsesweepstop"])
    ##pulsesweepstep = float(parameters["pulsesweepstep"])
    pulsevoltagerange = float(parameters["pulsevoltagerange"])
    
    query2182Apresent = int(instrument.query(":sour:pdel:nvpresent?"))
    if query2182Apresent == 0:
        print("2182A not present")
        instrument.disconnect()
        stop_time = time.time()  # Stop the timer...
        print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")
        sys.exit(1)

    invalid_parameters = False
    """if pulsehighcurrent == pulselowcurrent:
        print("High and low current cannot be the same")
        invalid_parameters = True"""
    if pulsecount < 1 or pulsecount > 65536:
        print("Number of readings must be in range [1, 65536]")
        invalid_parameters = True
    if volt_compliance < 0.1 or volt_compliance > 105:
        print("Voltage compliance must be in range [0.1, 105]")
        invalid_parameters = True
    if invalid_parameters:
        instrument.disconnect()
        stop_time = time.time()  # Stop the timer...
        print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")
        sys.exit(1)

    # Abort tests in the other modes
    instrument.write(":SOUR:SWE:ABOR")
    instrument.write(":SOUR:WAVE:ABOR")

    instrument.write("*RST")  # Reset the 6221
    time.sleep(2) # Wait 2 seconds
    instrument.write(":SYST:COMM:SERIAL:SEND \"*RST\"")  # Reset the 2182A
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

    
    
    instrument.write("pdel:swe ON")  # Set pulse sweep state
    instrument.write(":form:elem READ,TST,RNUM,SOUR")  # Set readings to be returned
    instrument.write(f":SOUR:CURR:COMP {volt_compliance}")  # Set voltage compliance
    instrument.write(":sour:swe:spac LIN")  # Set pulse sweep spacing
    instrument.write(f":sour:curr:start {pulsesweepstart}")  # Set pulse sweep start
    instrument.write(f":sour:curr:stop {pulsesweepstop}")  # Set pulse sweep stop
    instrument.write(f":sour:curr:poin {pulsecount}")  # Set pulse count
    instrument.write(f":sour:del {pulsedelay}")  # Set pulse delay
    instrument.write(f":sour:swe:rang BEST")  # Set sweep range # Best uses lowest range which will handle all sweep steps
    instrument.write(f":sour:pdel:lme {pulselowmeas}")  # Set number of low measurements
    instrument.write(f":sour:curr:comp {pulsecompliance}")  # Set pulse compliance
    #instrument.write(f"sour:curr:step {pulsesweepstep}")  # Set pulse sweep step
    instrument.write(f":SYST:COMM:SERIAL:SEND \":sens:volt:rang {pulsevoltagerange}\"")  # Set voltage measure range
    #instrument.write(f"sens:aver:wind 0")  # Set averaging window
    instrument.write("UNIT V")  # Set units (other options are OHMS, W, SIEM)

    
    time.sleep(2)
    

def read_data(instrument, num_readings: int):
    """Wait for instruments to finish measuring and read data"""
    # Wait for sweep to finish
    sweep_done = False
    data = []
    while not sweep_done:
        time.sleep(1)
        oper_byte_status = instrument.query(":STAT:OPER:EVEN?")  # Check the event register
        oper_byte_status = int(oper_byte_status)  # Convert decimal string to int
        sweep_done = oper_byte_status & (1 << 1)  # bit mask to check if sweep done

    # Get the measurements 1000 at a time
    for i in range((num_readings - 1) // 1000 + 1):
        if num_readings - i * 1000 > 1000:  # if more than 1000 readings left
            data_sel_count = 1000
        else:
            data_sel_count = num_readings - i * 1000

        # Transfer readings over GPIB
        raw_data = instrument.query(f":TRAC:DATA:SEL? {i * 1000},{data_sel_count}")
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
            "Number of Pulses",
            "pulsecount",
            "11",
            tooltip="Number of pulses in the sweep including the start and stop values",
        ),
        InstrumentOption(
            "Pulse Low Measurement",
            "pulselowmeas",
            "2",
            tooltip="Set number of low measurements. NRf = 1 or 2",
        ),
        InstrumentOption(
            "Pulse Compliance",
            "pulsecompliance",
            "100",
            tooltip="Voltage compliance must be in range [0.1, 105]",
        ),
        InstrumentOption(
            "Pulse Delay",
            "pulsedelay",
            "0.5",
            tooltip="Pulse settle time delay between current source change and measurement trigger.",
        ),
        InstrumentOption(
            "Pulse Voltage Range",
            "pulsevoltagerange",
            "100",
            tooltip="Valid Voltage Ranges: 0.01, 0.1, 1, 10 or 100",
        ),
        #InstrumentOption("Integration NPLCs", "integration_NPLCs", "5"),
        InstrumentOption(
            "Voltage Compliance",
            "volt_compliance",
            "100",
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
        inst_6221.write("SOUR:SWE:ABORT")  # Abort the test to prevent the output being left on
        inst_6221.disconnect()
        stop_time = time.time()  # Stop the timer...
        print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")
        sys.exit(1)

    #pulsecount = int(parameters["pulsecount"])
    #pulselowmeas = int(parameters["pulselowmeas"])
    num_readings = 65534
    # If user decides to abort or continue the program
    user_decision = input("Do you want to continue with the program? (yes/no): ")
    if user_decision.lower() == "no":
        print("Aborting the program as per user's request.")
        inst_6221.write(":SOUR:SWE:ABORT")  # Abort the test
        inst_6221.disconnect()
        stop_time = time.time()  # Stop the timer
        print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")
        sys.exit(1)
    experiment_setup(inst_6221, parameters, start_time)

    inst_6221.write(":sour:pdel:arm")  # Arm the test
    time.sleep(3)
    inst_6221.write(":init:imm")  # Start the test

    data = read_data(inst_6221, num_readings)

    date = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    csv_path = f".\\PulsedIVLinear_Measurements {date}.csv"
    write_csv(data, csv_path)

    inst_6221.write(":SOUR:SWE:ABORT")  # Abort the test to prevent the output being left on

    inst_6221.disconnect()

    stop_time = time.time()  # Stop the timer...

    # Notify the user of completion and the data streaming rate achieved.
    print("done")
    print(f"Elapsed Time: {(stop_time - start_time):0.3f}s")

    sys.exit(0)

if __name__ == "__main__":
    main()
