import os
import time
import datetime
import textwrap
from instrcomms import Communications
from instrgui import InstrumentOption, open_gui_return_input

DEBUG_PRINT_COMMANDS = True

# Ensure the parameters file is in the current working directory
SAVED_PARAMETERS_FILENAME = os.path.join(os.getcwd(), "sweep_parameters.txt")

def read_parameters(filename):
    with open(filename, "r") as file:
        lines = file.read().splitlines()
    return {
        "pulsehighcurrent": float(lines[0]),
        "pulselowcurrent": float(lines[1]),
        "pulsesweepspacing": lines[2],
        "pulsesweepstart": float(lines[3]),
        "pulsesweepstop": float(lines[4]),
        "pulsesweepstep": float(lines[5]),
        "pulsecount": int(lines[6]),
        "pulsesweeprange": lines[7],
        "pulsewidth": float(lines[8]),
        "pulsesweepstate": int(lines[9]),
        "pulselowmeas": int(lines[10]),
        "pulseinterval": float(lines[11]),
        "pulsecompliance": float(lines[12]),
        "pulsedelay": float(lines[13]),
        "filter_type": int(lines[14]),
        "filter_count": int(lines[15]),
        "pulsefilterstate": int(lines[16]),
        "pulsevoltagerange": float(lines[17]),
        "sweepdelay": float(lines[18]),
        "integration_NPLCs": float(lines[19]),
        "volt_compliance": float(lines[20]),
        "guarding_on": lines[21].strip().lower() == "true",
        "lowToEarth_on": lines[22].strip().lower() == "true",
    }

def validate_parameters(parameters):
    invalid_parameters = False
    if not (-105e-3 <= parameters["pulsehighcurrent"] <= 105e-3):
        print("High current must be in range [-105mA, 105mA]")
        invalid_parameters = True
    if not (-105e-3 <= parameters["pulselowcurrent"] <= 105e-3):
        print("Low current must be in range [-105mA, 105mA]")
        invalid_parameters = True
    if not (500e-6 <= parameters["pulsewidth"] <= 1000):
        print("Pulse width must be in range [500µs, 1000s]")
        invalid_parameters = True
    if not (0.1 <= parameters["volt_compliance"] <= 105):
        print("Voltage compliance must be in range [0.1V, 105V]")
        invalid_parameters = True
    if not (1 <= parameters["pulsecount"] <= 65536):
        print("Number of pulses must be in range [1, 65536]")
        invalid_parameters = True
    if not (1e-3 <= parameters["pulsedelay"] <= 9999.999):
        print("Pulse delay must be in range [1ms, 9999.999ms]")
        invalid_parameters = True
    if not (0.01 <= parameters["integration_NPLCs"] <= 50):
        print("Integration NPLCs must be in range [0.01, 50]")
        invalid_parameters = True
    if invalid_parameters:
        raise ValueError("Invalid parameters detected. Please correct the parameters and try again.")

def experiment_setup(instrument, parameters):
    """Set up instrument parameters for linear sweep test"""
    validate_parameters(parameters)
    
    filter_type = parameters["filter_type"]
    filter_count = parameters["filter_count"]
    integration_nplcs = parameters["integration_NPLCs"]
    volt_compliance = parameters["volt_compliance"]
    guarding_on = parameters["guarding_on"]
    low_to_earth_on = parameters["lowToEarth_on"]
    sweepdelay = parameters["sweepdelay"]
    pulsehighcurrent = parameters["pulsehighcurrent"]
    pulselowcurrent = parameters["pulselowcurrent"]
    pulsecount = parameters["pulsecount"]
    pulsesweeprange = parameters["pulsesweeprange"]
    pulsewidth = parameters["pulsewidth"]
    pulsedelay = parameters["pulsedelay"]
    pulsesweepstate = parameters["pulsesweepstate"]
    pulselowmeas = parameters["pulselowmeas"]
    pulseinterval = parameters["pulseinterval"]
    pulsecompliance = parameters["pulsecompliance"]
    pulsesweepspacing = parameters["pulsesweepspacing"]
    pulsesweepstart = parameters["pulsesweepstart"]
    pulsesweepstop = parameters["pulsesweepstop"]
    pulsesweepstep = parameters["pulsesweepstep"]
    pulsevoltagerange = parameters["pulsevoltagerange"]
    pulsefilterstate = parameters["pulsefilterstate"]

    query2182Apresent = int(instrument.query("sour:pdel:nvpresent?"))
    if query2182Apresent == 0:
        raise RuntimeError("2182A not present")

    # Abort tests in the other modes
    instrument.write("SOUR:SWE:ABOR")
    instrument.write("SOUR:WAVE:ABOR")

    instrument.write("*RST")  # Reset the 6221
    time.sleep(2)  # Wait 2 seconds
    instrument.write("SYST:COMM:SERIAL:SEND \"*RST\"")  # Reset the 2182A
    time.sleep(3)  # Wait 3 seconds

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

    sweepdelay = ((pulsecount * 1 / 50 - 6) / 1000)

    instrument.write(f"SOUR:DEL {sweepdelay}")  # Set delay between pulses
    instrument.write("form:elem READ,TST,RNUM,SOUR")  # Set readings to be returned
    instrument.write(f"SOUR:CURR:COMP {volt_compliance}")  # Set voltage compliance
    instrument.write(f"sour:pdel:high {pulsehighcurrent}")  # Set high current
    instrument.write(f"sour:pdel:low {pulselowcurrent}")  # Set low current
    instrument.write(f"sour:pdel:count {pulsecount}")  # Set num readings
    instrument.write(f"sour:pdel:rang {pulsesweeprange}")  # Set sweep range
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
        raise ValueError("Error: Invalid filter type parameter")

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

    parameters = read_parameters(SAVED_PARAMETERS_FILENAME)

    pulsecount = parameters["pulsecount"]
    pulselowmeas = parameters["pulselowmeas"]
    num_readings = pulsecount + (pulsecount * pulselowmeas)

    experiment_setup(inst_6221, parameters)

    inst_6221.write("sour:pdel:arm")  # Arm the test
    time.sleep(3)
    inst_6221.write("init:imm")  # Start the test

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

if __name__ == "__main__":
    main()
