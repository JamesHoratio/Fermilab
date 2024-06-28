import sys
import os
import csv
import time
import datetime
import pyvisa as visa
import argparse
import tkinter as tk
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import threading
import queue
import logging
import re
from keithley2600 import Keithley2600
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

DEBUG_PRINT_COMMANDS = True
INSTRUMENT_RESOURCE_STRING_6221 = 'TCPIP0::169.254.47.133::1394::SOCKET'
INSTRUMENT_RESOURCE_STRING_2182A = 'GPIB0::7::INSTR'
SAVED_PARAMETERS_FILENAME = "sweep_parameters.txt"
