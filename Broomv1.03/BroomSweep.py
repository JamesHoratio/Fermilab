import BroomInit
import json
import os
import sys
import time
import requests
import logging
import logging.handlers
import traceback
import subprocess
import re
import shutil
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator


class PulseIVSweep:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger('PulseIVSweep')
        self.logger.setLevel(logging.DEBUG)
        self.logger.info('PulseIVSweep initialized')
        self.data = []
        self.datafile = None
        self.datafilename = None


def main():
    config = BroomInit.InstrumentSetup('instrument_config.json')
    sweep = PulseIVSweep(config)
    config.initialize_and_setup_instrument()
    config.verify_instrument_setup()
    config.logger.info('Instrument setup verified')
    print('Instrument setup verified')
    

if __name__ == '__main__':
    main()
    