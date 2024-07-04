from sweep_functions import Keithley6221
from sweep_functions import showAllGraphs, draw
import time

def runProgram():
    keithley = Keithley6221()
    keithley.connect()
    keithley.getStatus()
    keithley.reset()
    keithley.pulseSweep()
    keithley.configureSweep()
    keithley.cleanBuffer()
    keithley.setBufSize()
    keithley.initialise()
    keithley.run()
    time.sleep(keithley.calcDataDelay() + 1)
    keithley.complete()
    keithley.dataProcessing()
    draw(keithley.U, keithley.I)


runProgram()
showAllGraphs()