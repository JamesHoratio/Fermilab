import matplotlib.pyplot as plt
import pyvisa
import random as random
import time
from config import *


fileCreationCounter = 0


class Keithley6221():
    """Keithley 6221 Instrument Class"""

    def __init__(self) -> None:
        self.rm = pyvisa.ResourceManager()
        self.connection = False
        self.delay = None
        self.start = 0
        self.stop = 0
        self.step = 0
        self.U = []
        self.I = []

    def connect(self) -> None:
        """Connect to the device at its address"""
        self.connection = self.rm.open_resource(INSTRUMENT_ADDRESS)
        print(f'Connected successfully!')

    def getStatus(self) -> None:
        """Querying Identification from instrument."""
        print(f'Information about this device: '
              f'{self.connection.query("*IDN?")}')

    def reset(self) -> None:
        """Restore default settings."""
        self.connection.write('*RST')
        print(f'Restored to default settings!')

    def setLinearStaircase(self) -> None:
        """Setting linear sweep."""
        self.connection.write(f'SOUR:SWE:SPAC LIN')

    def setStartCurrent(self) -> None:
        """Setting the initial current value."""
        startCurrent = input('Set initial current: ')
        self.connection.write(f'SOUR:CURR:STAR ' + startCurrent)
        self.start = float(startCurrent)

    def setStopCurrent(self) -> None:
        """Setting the final current value = maxiumum current amplitude"""
        stopCurrent = input('Set stop current: ')
        self.connection.write(f'SOUR:CURR:STOP ' + stopCurrent)
        self.stop = float(stopCurrent)

    def setStep(self) -> None:
        """Setting the current amplitude increasing step."""
        step = input('Set amplitude increase stepsize: ')
        self.connection.write(f'SOUR:CURR:STEP ' + step)
        self.step = float(step)

    def calcDataDelay(self) -> int:
        """Calculation of current generation time before shutdown."""
        timeDelay = ((self.stop - self.start) / self.step) * self.delay
        return round(timeDelay)

    def setDelay(self) -> None:
        """Setting the wait time between pulses."""
        delay = input('Set the pulse delay: ')
        self.connection.write(f'SOUR:DEL ' + delay)
        self.delay = float(delay)

    def setSpan(self) -> None:
        """
        Set the source range.

        [BEST] -- Uses optimal range to accomodate all sweep steps
        """
        self.connection.write(f'SOUR:PDEL:RANG BEST')

    def setCurrentCompliance(self) -> None:
        """Set output voltage limitation."""
        currentCompliance = input('Set voltage limit: ')
        self.connection.write(f'SOUR:CURR:COMP ' + currentCompliance)

    def setTriaxOutputLow(self) -> None:
        """Low to earth grounding output.

            [ON] -- Enable output
            [OFF] -- Disable output
            """
        triaxOutputLow = input('Output to ground: ')
        self.connection.write(f'OUTP:LTE ' + triaxOutputLow)

    def setLowSignal(self) -> None:
        """Setting the signal level low"""
        self.connection.write(f'SOUR:PDEL:LOW 0')

    def setHighSignal(self) -> None:
        """Setting the signal level high (optional)."""
        highSignal = input('Set the signal level high to: ')
        self.connection.write(f'SOUR:PDEL:HIGH ' + highSignal)

    def setImpulseInterval(self) -> None:
        """Setting the pulse interval."""
        impulseInterval = input('Set the pulse interval: ')
        self.connection.write(f'SOUR:PDEL:INT ' + impulseInterval)

    def setWidth(self) -> None:
        """Setting the pulse width."""
        width = input('Set the pulse width: ')
        self.connection.write(f'SOUR:PDEL:WIDT ' + width)

    def setSweepMode(self) -> None:
        """Initializing the sweep function."""
        self.connection.write(f'SOUR:PDEL:SWE ON')

    def setDelayOfMode(self) -> None:
        """Setting the sweep delay time."""
        delayOfMode = input('Set the mode delay: ')
        self.connection.write(f'SOUR:PDEL:SDEL ' + delayOfMode)

    def setPulseCount(self) -> None:
        """Meter setting. Sets the buffer size."""
        pulseCount = input('Set the number of pulses: ')
        self.connection.write('SOUR:PDEL:COUN ' + pulseCount)

    def setBufSize(self) -> None:
        """Setting the buffer size."""
        self.connection.write('TRAC:POIN 5000')

    def cleanBuffer(self) -> None:
        """Clearning buffer"""
        self.connection.write('TRAC:CLE')

    def setInterruption(self) -> None:
        """
        Abort when parameters go beyond compliance level.

        [ON] -- Function enabled
        [OFF] -- Function disabled
        """
        turnInterruption = input('Termination: ')
        self.connection.write('TRAC:DCON:CAB ' + turnInterruption)

    def initialise(self) -> None:
        """Initializes the pulse delta test."""
        self.connection.write('SOUR:PDEL:ARM')

    def run(self) -> None:
        """Runs a pulse delta test."""
        print('The process has started...')
        self.connection.write('INIT:IMM')

        # Waiting for the process to complete and not interrupting it
        time.sleep(self.calcDataDelay() + 1)
        print("The process is complete!")

    def complete(self) -> None:
        """Stopping the pulse delta test."""
        self.connection.write('SOUR:SWE:ABOR')

    def dataProcessing(self) -> None:
        """Reading measurements from the Keithley6221 buffer."""
        time.sleep(5)
        data = str(self.connection.query('TRAC:DATA?'))
        dataList = data.split(",")[::2]

        for number in dataList:
            self.U.append(float(number))

        self.I = [self.start + i * self.step for i in range(len(self.U))]

        # Big data takes longer to process
        time.sleep(5)

    def configureSweep(self) -> None:
        """Setting values in linear step module."""
        self.setLinearStaircase()
        self.setStartCurrent()
        self.setStopCurrent()
        self.setStep()
        self.setSpan()
        self.setCurrentCompliance()
        self.setDelay()
        self.setTriaxOutputLow()

    def pulseSweep(self) -> None:
        """Setting values in pulse delta test mode."""
        self.setLowSignal()
        self.setWidth()
        self.setDelayOfMode()
        self.setSweepMode()
        self.setPulseCount()


def saveToFile(U, I, fileNumber) -> None:
    """Saving readings from the device to a file."""
    name = input('Enter file name: ')
    fileNumber += 1
    with open(f'{name}{fileNumber}.txt', "a", encoding="utf-8") as f:
        # Left column -- voltage, right -- current.
        # f.write("{:^15}{:^35}\n".format("U", "I"))
        for u, i in zip(U, I):
            f.write("{:<25.13f}{:<25.13f}\n".format(u, i))
        f.close()


def draw(U, I) -> None:
    """
    Plotting a graph on the measured data.

    You can do the following with the graph (when viewing it):
        Move with the cursor over the graph
        Zoom in
        Change the viewing settings (e.g. shift sideways)
        Save
        Reset the settings described above
    """

    color = ('#004C97')

    plt.title('Volt-ampere characteristic')
    plt.xlabel('Current (A)')
    plt.ylabel('Voltage (V)')
    plt.plot(I, U, c=color)


def showAllGraphs() -> None:
    """Shows all plots on one window for clarity."""
    plt.show()