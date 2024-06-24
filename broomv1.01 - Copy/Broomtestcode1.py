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
import os
import threading
import queue
import time
import pdb
import re
import logging
import pyvisa as visa
from keithley2600 import Keithley2600
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)

DEBUG_PRINT_COMMANDS = True
INSTRUMENT_RESOURCE_STRING_6221 = 'TCPIP0::169.254.47.133::1394::SOCKET'  # Change this to your 6221's resource string
INSTRUMENT_RESOURCE_STRING_2182A = 'GPIB0::7::INSTR'  # Change this to your 2182A's resource string
SAVED_PARAMETERS_FILENAME = ("sweep_parameters.txt")

class K6221():
    def __init__(self):
        self.K6221Address=INSTRUMENT_RESOURCE_STRING_6221
        self.connected = self.connect()
        self.sm.write_termination='\n'
        self.sm.read_termination='\n'
        self.sm.chunk_size=102400
        self.sm.write(':SYST:PRES')
        time.sleep(1)
        self.sm.write('FORM:ELEM READ') ## send out only the reading
        self.sm.write(':SYST:COMM:SER:BAUD 19200') ### set baud
        self.sm.write(':SYST:COMM:SER:SEND "*RST"') ### reset 2182
        time.sleep(1)
        self.sm.write(':SYST:COMM:SER:SEND "*CLS"') ### reset 2182
        time.sleep(0.2)
        self.sm.write(':SYST:COMM:SER:SEND ":INIT:CONT OFF;:ABORT"') ### init off
        time.sleep(0.2)
        self.sm.write(':SYST:COMM:SER:SEND ":SYST:BEEP:STAT OFF"') ### init off
        time.sleep(0.2)
        self.sm.write('SYST:COMM:SER:SEND "FORM:ELEM READ"') ## send out only the reading
        time.sleep(0.2)

    def connect(self):
        try:
            rm = visa.ResourceManager('@py')
            self.sm=rm.open_resource(self.K6221Address) ## setting a delay between write and query
            self.sm.write_termination='\n'
            self.sm.read_termination='\n'
            self.sm.chunk_size=102400
            logging.debug('Connected to 6221 at ' + K6221Address)
            return True
        except Exception:
            logging.error('Unable to connect to 6221 at ' + K6221Address)
            return False
############## configure source smu#####
    def setSourceMode(self,chan,param,slim,comp):
        self.sm.write(':SOUR:SWE:ABOR')
        if slim.lower() == 'auto': ## set range
            self.sm.write('SOUR:CURR:RANG:AUTO ON')
        else:
            self.sm.write('SOUR:CURR:RANG '+slim)
        if comp.lower() == 'auto': ## set range
            self.sm.write('SOUR:CURR:COMP '+str(100)) ## set compliance of voltage to maximum
        else:
            self.sm.write('SOUR:CURR:COMP '+comp) ## set compliance 
        self.sm.write(':OUTP ON') ## set compliance 

    def setSenseMode(self,chan,param,mlim,nplc,aver): ## put only generic sensing modes
        ### since, 2182 is connected via serial port, the command must be routed.
        ####configure measure SMU
        self.sm.write(':SYST:CLE') ## clear the interface
        self.sm.write(':SYST:COMM:SER:SEND "SENS:CHAN 1"') ##set channel 1 for measurements
        time.sleep(0.2)
        self.sm.write(':SYST:COMM:SER:SEND "SENS:FUNC \'VOLT:DC\'"') ##set channel 1 for measurements
        time.sleep(0.2)
        self.sm.write(':SYST:COMM:SER:SEND "SENS:VOLT:NPLC ' + str(nplc) + '"') ##set channel 1 for measurements
        time.sleep(0.2)
        self.sm.write(':SYST:COMM:SER:SEND ":TRAC:CLE"') ## clean the trace
        time.sleep(0.2)
        if mlim.lower() == 'auto':
            self.sm.write('SYST:COMM:SER:SEND "SENS:VOLT:RANG:AUTO ON"') ## set auto range
        else:
            self.sm.write('SYST:COMM:SER:SEND "SENS:VOLT:RANG '+ mlim + '"') ## set voltage range
        time.sleep(0.2)
        self.sm.write(':SYST:COMM:SER:SEND ":SAMP:COUN ' + str(aver) +'"') ## anytime read that many data

    def IVSweep(self,dcivData): # smu1 is source and smu2 is sense
        start=float(dcivData["sStart"])
        stop = float(dcivData["sEnd"])
        points = int(dcivData["sPoints"])
        loop = dcivData["Loop"]
        LoopBiDir = dcivData["LoopBiDir"]
        aver = int(dcivData["aver"])
        nplc = float(dcivData["nplc"])
        sourceLimit = dcivData["slimit"]
        measureLimit= dcivData["mlimit"]
        stepPeriod=dcivData["sDel"]
        pWidth=dcivData["pWidth"]
        pPeriod=dcivData["pPeriod"]
        pulse=dcivData["Pulse"]
        ######################## Set source settings ###################
        self.sm.write(':SOUR:SWE:ABOR') ### abort any sweep
        self.setSourceMode('1','I',sourceLimit,measureLimit)
        self.setSenseMode('1','V',measureLimit,nplc,aver)
        #### General measurement settings
        if loop: 
            if LoopBiDir:
                sweepList = np.concatenate([np.linspace(0,stop,points),np.linspace(stop,0,points),np.linspace(0,-stop,points),np.linspace(-stop,0,points)])
            else:
                sweepList = np.concatenate([np.linspace(start,stop,points),np.linspace(stop,start,points)])
        else:
            sweepList = np.linspace(start,stop,points)
        tPoints = len(sweepList)
        logging.info('sweep list' + str(sweepList))
        currStep = (stop-start)/points
        self.sm.write(':SOUR:SWE:SPAC LIST') ## going for linear always. if too many points, its failing 
        self.sm.write(':SOUR:SWE:RANG AUTO') # auto limit
        self.sm.write(':SOUR:SWE:CAB OFF') # remove compliance off
 ################ setting sweep points
        print(self.sm.query('SOUR:LIST:CURR?'))
        self.sm.write('SOUR:SWE:COUN 1') ## just one sweep
        if measureLimit.lower() == 'auto':
            self.sm.write('SOUR:CURR:COMP 100') ## just one sweep
        else:
            self.sm.write('SOUR:CURR:COMP ' +str(measureLimit)) ## just one sweep
        self.sm.write(':TRAC:CLE') ## clear trace of 6221
        self.sm.write(':SYST:COMM:SER:SEND ":SENS:VOLT:LPAS OFF"') ### reset 2182
        time.sleep(0.1)
        self.sm.write(':SYST:COMM:SER:SEND ":SENS:VOLT:DFIL OFF"') ### reset 2182
        time.sleep(0.1)
        self.sm.write(':SYST:COMM:SER:SEND ":TRAC:CLE"') ### reset 2182
        time.sleep(1)
        self.sm.write(':TRAC:CLE') 
        self.sm.write(':TRAC:FEED SENS') ### reset 2182
        self.sm.write(':TRAC:FEED:CONT NEXT') ### reset 2182
        self.sm.write(':TRAC:POIN ' + str(tPoints)) 
        if pulse:
            self.sm.write('SOUR:LIST:CURR ' + str(start)) ## clears the list and adds 0
            self.sm.write('SOUR:LIST:DEL ' + str(pPeriod)) ## clears the list and adds 0
            for i in range(1,tPoints):
                self.sm.write('SOUR:LIST:CURR:APP ' + str(sweepList[i]))
                self.sm.write('SOUR:LIST:DEL:APP ' + str(pPeriod))
            self.sm.write(':SOUR:SWE:RANG BEST') # limit set to the highest sweep value
           
            self.sm.write(':SOUR:PDEL:WIDT ' + str(pWidth)) 
            self.sm.write(':SOUR:PDEL:SDEL 100E-6') ## I think again this is only for fixed output
            self.sm.write(':SOUR:PDEL:LOW 0') 
            self.sm.write(':SOUR:PDEL:SWE ON') 
            self.sm.write(':SOUR:PDEL:LME 2') 
            self.sm.write(':SOUR:PDEL:ARM')
            time.sleep(1)
            self.sm.write(':INIT:IMM')
            time.sleep(tPoints*(float(pPeriod) + float(pWidth) + 0.1) + 5) ### waiting for just the exact time was not being enough
            self.sm.write('SOUR:SWE:ABOR')
            values=self.getTraceData('1','I',tPoints)
        else: ### normal sweeping
            self.sm.write('SOUR:LIST:CURR ' + str(start)) ## clears the list and adds 0
            self.sm.write('SOUR:LIST:DEL ' + str(stepPeriod)) ## clears the list and adds 0
            for i in range(1,tPoints):
                self.sm.write('SOUR:LIST:CURR:APP ' + str(sweepList[i]))
                self.sm.write('SOUR:LIST:DEL:APP ' + str(stepPeriod))
            self.sm.write(':SOUR:SWE:RANG BEST') # limit set to the highest sweep value
            self.sm.write(':TRIG:SOUR TLINK')
            self.sm.write(':TRIG:DIR SOUR')
            self.sm.write(':TRIG:OLIN 2')
            self.sm.write(':TRIG:ILIN 1')
            self.sm.write(':TRIG:OUTP DEL')
            self.sm.write(':TRAC:CLE') ### reset 2182
            self.sm.write(':SYST:COMM:SER:SEND ":SENS:VOLT:LPAS OFF"') ### reset 2182
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":SENS:VOLT:DFIL OFF"') ### reset 2182
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRAC:CLE"') ### reset 2182
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRAC:FEED SENS"') ### reset 2182
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRAC:POIN ' + str(tPoints) +'"') ### reset 2182
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRIG:SOUR EXT"') ### reset 2182
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRIG:COUN ' + str(tPoints) +'"') ### reset 2182
            time.sleep(0.1)
            self.sm.write(':SYST:COMM:SER:SEND ":TRAC:FEED:CONT NEXT"') ### reset 2182
            time.sleep(0.1)
            self.sm.write(':SOUR:SWE:ARM')
            time.sleep(1)
            self.sm.write(':INIT:IMM')
            self.sm.write(':SYST:COMM:SER:SEND ":INIT"') ### reset 2182
            time.sleep(tPoints*(float(stepPeriod) + 0.1) + 5)
            self.sm.write('SOUR:SWE:ABOR')
            self.turnOffOutputs()
            time.sleep(1)
            #self.sm.write(':SYST:COMM:SER:SEND ":TRAC:DATA?"')
            #time.sleep(5)
            #values=np.array(self.sm.query_ascii_values(':SYST:COMM:SER:ENT?'))
            values=self.get2182TraceData('1','I',tPoints)
        print(values)
        logging.info('got these values\n' + str(values))
        measuredValues=resultBook()
        measuredValues.points = len(values)
        measuredValues.I = sweepList
        measuredValues.V = values

        return measuredValues

    def getErrors(self):
        err = self.sm.query(":syst:err?")
        logging.info(err)
        #self.sm.close()
        return err
    def preset(self):
        self.sm.write(':SYST:COMM:SER:SEND ":SYST:PRES"') ### reset 2182
        self.sm.write(':SYST:PRES') ### reset 6221
    def turnOffOutputs(self):
        self.sm.write(':OUTP OFF')

    def doMeasure(self,smu,param,aver):
        mData = []
        self.sm.write(':SYST:COMM:SER:SEND ":READ?"') ## do one read into trace buffers 
        waitingForData=True
        timeSlept=0
        while waitingForData:
            if len(mData) >= aver:
                logging.info('got all Data')
                waitingForData=False
            elif timeSlept > 30:
                logging.warning('timed out')
                waitingForData=False
            else: 
                try:
                    time.sleep(0.2)
                    resp = self.sm.query(':SYST:COMM:SER:ENT?')
                    mData=np.append(mData,np.asarray(re.findall('[+-][0-9\.]+E[+-][0-9]+',resp),dtype=float))
                    logging.info('Adding data' + resp)
                except Exception as err:
                    logging.warning('Unable to add the data' + resp)
                timeSlept +=0.5
                time.sleep(0.3)
        return np.mean(mData)

    def doSource(self,smu,param,value): ## no use for other values. It can only output current
        self.sm.write(':CURR ' + str(value))
        return 
    def writeK2182(self,comm):
        return(self.sm.write(':SYST:COMM:SER:SEND "' + comm + '"'))
    def queryK2182(self,comm):
        self.sm.write(':SYST:COMM:SER:SEND "' + comm + '"')
        time.sleep(0.2)
        return(self.sm.query(':SYST:COMM:SER:ENT?'))

    def get2182TraceData(self,smu,param,tPoints):
        mData = []
        time.sleep(5)
        self.sm.write(':SYST:COMM:SER:SEND ":TRAC:DATA?"')
        time.sleep(1)
        waitingForData=True
        timeSlept=0
        while waitingForData:
            if len(mData) >= tPoints:
                logging.info('got all Data')
                waitingForData=False
            elif timeSlept > 10:
                logging.warning('timed out')
                waitingForData=False
            else: 
                try:
                    time.sleep(0.2)
                    resp = self.sm.query(':SYST:COMM:SER:ENT?')
                    logging.info('Read from instrument: ' + resp)
                    mData=np.append(mData,np.asarray(re.findall('[+-][0-9\.]+E[+-][0-9]+',resp),dtype=float))
                    logging.info('Adding data' + resp)
                except ValueError:
                    logging.warning('Unable to add the data' + resp)
                timeSlept +=0.5
                time.sleep(0.3)
        return mData
    
    ################ get data from 6221 ##############
    def getTraceData(self,smu,param,tPoints):
        mData = []
        waitingForData=True
        timeSlept=0
        while waitingForData:
            if len(mData) >= tPoints:
                logging.info('got all Data')
                waitingForData=False
            elif timeSlept > 30:
                logging.warning('timed out. Leaving with either empty or partial data of length ' + str(len(mData)))
                waitingForData=False
            else:
                try:
                    resp = self.sm.query(':TRAC:DATA?')
                    mData=np.append(mData,np.asarray(re.findall('[+-][0-9\.]+E[+-][0-9]+',resp),dtype=float))
                    logging.info('Adding data' + resp)
                except Exception as e:
                    logging.warning('Unable to add the data. Got this  ' + resp)
                timeSlept +=0.5
                time.sleep(0.5)
        return mData

class resultBook:
    def __init__(self):
        logging.info('A result book is created')

class measurements:
    def __init__(self):
        self.active = False
        ################# Queue to hold the measured data from measurement threads ###########
        self.measureData = queue.Queue()
    def runMeasurement(self,measFrame,configFrame,PF):
        timeElapsed=0
        while self.active: #### is another measurement is running - wait
            if timeElapsed >5:
                return
            else:
                print('Measurement running. Waiting for it to finish')
                time.sleep(1)
                timeElapsed +=1
        measData = measFrame.getButtonValues()
        configData = configFrame.getButtonValues()
        measureFile = configData["WD"] + '/' + configData["mName"] + ".csv"
        errFile = configData["WD"] + '/' + configData["mName"] + "err.txt"
        self.MD = configFrame.MD ### get the measurement tool instance
        self.measureData.queue.clear()
        PF.showRunning()

        if configData["mt"] == 'iv':
            plotData = np.zeros((1,2))
            PF.clearPlot()
            f1 = open(measureFile,'w')
            f1.write("Voltage,Current\n")
            t1=threading.Thread(target=self.runDCIV, args=(measData,))
            t1.start()
            while t1.is_alive():
                time.sleep(3)
                while not self.measureData.empty():
                    plotData = self.measureData.get()
                    f1.write(str(plotData[0]) + ',' + str(plotData[1]) + '\n')
                    PF.addPoint(plotData[0],plotData[1],'*k')
                PF.flushPlot()
            #inArray = np.loadtxt('data.csv',delimiter=',')
            t1.join()
            f1.close()
        else:
            logging.error('Measurement type not supported')
            print('Measurement type not supported')
            PF.removeRunning()
        #get all errors
        err=self.MD.getErrors()
        f2 = open(errFile,'w')
        for line in err:
            f2.write(line + '\n')
        f2.close()

    def runDCIV(self,dcivData):
        self.active = True
        measured = self.MD.IVSweep(dcivData) ### got the data in the format of a result book
        self.MD.turnOffOutputs() 
        self.active = False
        for i in range(measured.points):
            self.measureData.put([measured.V[i],measured.I[i]])
        ### set outputs to off state

class configFrame(tk.Frame):
    def __init__(self,parent,PF):
        super().__init__(parent)
        self.mt = tk.StringVar()
        self.iName = tk.StringVar()
        rCount = 0
        #### Measurement Name ###################
        label_a = tk.Label(master=self, text="Measurement Configurations", font = ('Calibri',12,'bold'))
        label_a.grid(row=rCount,column = 0)
        rCount = rCount + 1
        lbl_mName = tk.Label(self, text="Measurement Name")
        lbl_mName.grid(row=rCount,column=0,sticky='e')
        self.mName = tk.Entry(master=self, width=10)
        self.mName.grid(row=rCount,column=1,sticky='w')
        rCount = rCount + 1
        #### Working director
        lbl_WD = tk.Label(self, text="Working Directory")
        lbl_WD.grid(row=rCount,column=0,sticky='e')
        self.WD = tk.Entry(master=self, width=10)
        self.WD.grid(row=rCount,column=1,sticky='w')
        rCount = rCount + 1
        #### Instrument Name ###################
        lbl_Iname = tk.Label(master=self, text="Instrument Name")
        lbl_Iname.grid(row=rCount,column=0,sticky='e')
        r1 = tk.Radiobutton(self, text="Keithley 2636B", variable=self.iName, value='K2636B')
        r1.grid(row=rCount,column=1)
        r1 = tk.Radiobutton(self, text="Keysight B2912B", variable=self.iName, value='B2912B')
        r1.grid(row=rCount,column=2)
        r1 = tk.Radiobutton(self, text="Keithley 6221+2182A", variable=self.iName, value='K6221')
        r1.grid(row=rCount,column=3)
        rCount = rCount + 1
        #### Measurement Type ################
        lbl_mt = tk.Label(master=self, text="measurement type")
        lbl_mt.grid(row=rCount,column=0,sticky='e')
        r1 = tk.Radiobutton(self, text="DC IV", variable=self.mt, value='iv')
        r1.grid(row=rCount,column=1)
        r1 = tk.Radiobutton(self, text="MOSFET IDVG", variable=self.mt, value='MOSFET')
        r1.grid(row=rCount,column=2)
        r1 = tk.Radiobutton(self, text="IV-T", variable=self.mt, value='IVT')
        r1.grid(row=rCount,column=3)
        r1 = tk.Radiobutton(self, text="dIdV", variable=self.mt, value='dIdV')
        r1.grid(row=rCount,column=4)
        rCount = rCount + 1
        bt = tk.Button(master=self,text='Set Defaults',command=self.setDefaults)
        bt.grid(row = rCount,column = 0)
        rCount = rCount + 1
        lbl_mp = tk.Label(master=self, text="Press Config to configure measurements")
        lbl_mp.grid(row =rCount,column = 0,sticky = 'e')
        switch=tk.Button(self,text='Config',command= parent.switchFrame)
        switch.grid(row = rCount,column = 1,sticky = 'e')
    def setDefaults(self):
        self.iName.set('K2636B')
        self.mt.set('iv')
        self.mName.delete(0,tk.END)
        self.mName.insert(0,'test')
        self.WD.delete(0,tk.END)
        self.WD.insert(0,'./')
    def getButtonValues(self):
        configData = {
        "inst":self.iName.get(),
        "mt":self.mt.get(),
        "mName":self.mName.get(),
        "WD":self.WD.get()
        }
        return configData

class DCIVFrame(tk.Frame):
    def __init__(self,parent, configFrame, plotFrame):
        self.source = tk.StringVar()
        self.sense = tk.StringVar()
        self.mp = tk.StringVar()
        self.sp = tk.StringVar()
        self.iName = tk.StringVar()
        self.Pulse = tk.BooleanVar()
        self.Loop = tk.BooleanVar()
        self.LoopBiDir = tk.BooleanVar()
        super().__init__(parent)
        self.measure = measurements()
        #### Smu to be used ################
        rCount = 0
        lbl_source = tk.Label(master=self, text="DC IV Control Settings")
        lbl_source.grid(row=rCount,column=0,sticky='e')
        rCount = rCount + 1
        lbl_source = tk.Label(master=self, text="Source SMU")
        lbl_source.grid(row=rCount,column=0,sticky='e')
        r1 = tk.Radiobutton(self, text="SMU A", variable=self.source, value='a')
        r1.grid(row=rCount,column=1)
        r1 = tk.Radiobutton(self, text="SMU B", variable=self.source, value='b')
        r1.grid(row=rCount,column=2)
        rCount = rCount + 1
        lbl_source = tk.Label(master=self, text="Sense SMU")
        lbl_source.grid(row=rCount,column=0,sticky='e')
        r1 = tk.Radiobutton(self, text="SMU A", variable=self.sense, value='a')
        r1.grid(row=rCount,column=1)
        r1 = tk.Radiobutton(self, text="SMU B", variable=self.sense, value='b')
        r1.grid(row=rCount,column=2)
        rCount = rCount + 1
        
        #### Source start ###################
        lbl_sStart = tk.Label(master=self, text="Source Start (V/A)")
        lbl_sStart.grid(row=rCount,column=0,sticky='e')
        self.sStart = tk.Entry(master=self, width=10)
        self.sStart.grid(row=rCount,column=1,sticky='e')
        rCount = rCount + 1

        #### Averaging ###################
        lbl_sEnd = tk.Label(master=self, text="Source End (V/A)")
        lbl_sEnd.grid(row=rCount,column=0,sticky='e')
        self.sEnd = tk.Entry(master=self, width=10)
        self.sEnd.grid(row=rCount,column=1,sticky='e')
        rCount = rCount + 1
        #### Averaging ###################
        lbl_sPoints = tk.Label(master=self, text="Points")
        lbl_sPoints.grid(row=rCount,column=0,sticky='e')
        self.sPoints = tk.Entry(master=self, width=10)
        self.sPoints.grid(row=rCount,column=1,sticky='w')
        lbl_sPoints = tk.Label(master=self, text="sweep delay")
        lbl_sPoints.grid(row=rCount,column=2,sticky='e')
        self.sDel = tk.Entry(master=self, width=10)
        self.sDel.grid(row=rCount,column=3,sticky='w')
        rCount = rCount + 1
        #### Averaging ###################
        lbl_mAverage = tk.Label(master=self, text="Manual Averaging count")
        lbl_mAverage.grid(row=rCount,column=0,sticky='e')
        self.mAverage = tk.Entry(master=self, width=10)
        self.mAverage.grid(row=rCount,column=1,sticky='e')
        lbl_nAverage = tk.Label(master=self, text=" NPLC (20ms*)")
        lbl_nAverage.grid(row=rCount,column=2,sticky='e')
        self.nAverage = tk.Entry(master=self, width=10)
        self.nAverage.grid(row=rCount,column=3,sticky='e')
        rCount = rCount + 1
        #### Loop parameter ################
        lbl_sp = tk.Label(master=self, text="Loop")
        lbl_sp.grid(row=rCount,column=0,sticky='e')
        r1 = tk.Radiobutton(self, text="True", variable=self.Loop, value=1)
        r1.grid(row=rCount,column=1)
        r1 = tk.Radiobutton(self, text="False", variable=self.Loop, value=0)
        r1.grid(row=rCount,column=2)
        c1=tk.Checkbutton(self,text="BiDirect",variable=self.LoopBiDir,onvalue=True,offvalue=False)
        c1.grid(row=rCount,column=3)
        rCount = rCount + 1
        #### Source parameter ################
        lbl_sp = tk.Label(master=self, text="Pulsing")
        lbl_sp.grid(row=rCount,column=0,sticky='e')
        r1 = tk.Radiobutton(self, text="True", variable=self.Pulse, value=1)
        r1.grid(row=rCount,column=1)
        r1 = tk.Radiobutton(self, text="False", variable=self.Pulse, value=0)
        r1.grid(row=rCount,column=2)
        rCount = rCount + 1
        #### pulse period ###################
        lbl_pPeriod = tk.Label(master=self, text="pulse period (S)")
        lbl_pPeriod.grid(row=rCount,column=0,sticky='e')
        self.pPeriod = tk.Entry(master=self, width=10)
        self.pPeriod.grid(row=rCount,column=1,sticky='e')
        #### Source limit ###################
        lbl_pWidth = tk.Label(master=self, text="pulse width (S)")
        lbl_pWidth.grid(row=rCount,column=2,sticky='e')
        self.pWidth = tk.Entry(master=self, width=10)
        self.pWidth.grid(row=rCount,column=3,sticky='e')
        rCount = rCount + 1

        #### Source parameter ################
        lbl_sp = tk.Label(master=self, text="Source parameter")
        lbl_sp.grid(row=rCount,column=0,sticky='e')
        r1 = tk.Radiobutton(self, text="voltage", variable=self.sp, value='V')
        r1.grid(row=rCount,column=1)
        r1 = tk.Radiobutton(self, text="current", variable=self.sp, value='I')
        r1.grid(row=rCount,column=2)
        rCount = rCount + 1
        #### Smu to be used ################
        lbl_mp = tk.Label(master=self, text="measure parameter")
        lbl_mp.grid(row=rCount,column=0,sticky='e')
        r1 = tk.Radiobutton(self, text="voltage", variable=self.mp, value='V')
        r1.grid(row=rCount,column=1)
        r1 = tk.Radiobutton(self, text="current", variable=self.mp, value='I')
        r1.grid(row=rCount,column=2)
        rCount = rCount + 1
        #### Limits and ranges #########################
        #### Source limit ###################
        lbl_slimit = tk.Label(master=self, text="source limit (V/A)")
        lbl_slimit.grid(row=rCount,column=0,sticky='e')
        self.slimit = tk.Entry(master=self, width=10)
        self.slimit.grid(row=rCount,column=1,sticky='w')
        rCount = rCount + 1
        #### measure limit ###################
        lbl_mlimit = tk.Label(master=self, text="measure limit (V/A)")
        lbl_mlimit.grid(row=rCount,column=0,sticky='e')
        self.mlimit = tk.Entry(master=self, width=10)
        self.mlimit.insert(0,'100E-3')
        self.mlimit.grid(row=rCount,column=1,sticky='w')
        rCount = rCount + 1

        btn_run = tk.Button(master=self, text="Run",command=lambda: self.measure.runMeasurement(self,configFrame,plotFrame))
        btn_run.grid(row=rCount,column=0)
        bt = tk.Button(master=self,text='Set Defaults',command=self.setDefaults)
        bt.grid(row = rCount,column = 1)
    def setDefaults(self):
        self.mlimit.delete(0,tk.END)
        self.mlimit.insert(0,'Auto')
        self.slimit.delete(0,tk.END)
        self.slimit.insert(0,'100E-3')
        self.sEnd.delete(0,tk.END)
        self.sEnd.insert(0,'100E-3')
        self.sStart.delete(0,tk.END)
        self.sStart.insert(0,'0')
        self.sPoints.delete(0,tk.END)
        self.sDel.delete(0,tk.END)
        self.pWidth.delete(0,tk.END)
        self.pWidth.insert(0,'10E-3')
        self.pPeriod.delete(0,tk.END)
        self.pPeriod.insert(0,'1')
        self.sStart.delete(0,tk.END)
        self.sStart.insert(0,'0')
        self.sPoints.insert(0,'10')
        self.sDel.insert(0,'100E-3')
        self.mAverage.delete(0,tk.END)
        self.mAverage.insert(0,'1')
        self.nAverage.delete(0,tk.END)
        self.nAverage.insert(0,'5')
        self.source.set('a')
        self.sense.set('a')
        self.mp.set('I')
        self.sp.set('V')
        self.Pulse.set(False)
        self.Loop.set(False)
        self.LoopBiDir.set(False)
    def getButtonValues(self):
        dcivData = {
            "source":self.source.get(),
            "sense":self.sense.get(),
            "sParam":self.sp.get(),
            "mParam":self.mp.get(),
            "sEnd":self.sEnd.get(),
            "sStart":self.sStart.get(),
            "sPoints":self.sPoints.get(),
            "sDel":self.sDel.get(),
            "Loop":self.Loop.get(),
            "LoopBiDir":self.LoopBiDir.get(),
            "Pulse":self.Pulse.get(),
            "pPeriod":self.pPeriod.get(),
            "pWidth":self.pWidth.get(),
            "aver":self.mAverage.get(),
            "nplc":self.nAverage.get(),
            "slimit":self.slimit.get(),
            "mlimit":self.mlimit.get(),
        }
        return dcivData

class controlFrame(tk.Frame):
    def __init__(self,parent,PF):
        super().__init__(parent,highlightbackground="black", highlightthickness=1, width=100, height=100, bd=0)
        self.PF = PF
        self.CF = configFrame(self,PF)
        self.DCIV = DCIVFrame(self, self.CF, PF)
        self.dIdV = dIdVFrame(self, self.CF, PF)
        self.MOSFET = MOSFETFrame(self, self.CF, PF)
        self.IVT = IVTFrame(self, self.CF, PF)
        self.CF.grid(row = 1,column=0)
        self.CF.setDefaults()
        self.bottomFrame = tk.Frame(self)
        self.bottomFrame.grid(row=2,column=0)
    def switchFrame(self):
        cfData = self.CF.getButtonValues()
        self.bottomFrame.grid_forget()
        if cfData["mt"] == 'iv':
            self.bottomFrame=self.DCIV
        elif cfData["mt"] == 'MOSFET':
            self.bottomFrame=self.MOSFET
        elif cfData["mt"] == 'IVT':
            self.bottomFrame=self.IVT
        elif cfData["mt"] == 'dIdV':
            self.bottomFrame=self.dIdV
        self.bottomFrame.tkraise()
        self.bottomFrame.grid(row=2,column = 0, padx = 10)
        self.bottomFrame.setDefaults()
        ###### instantiate the instruments ###############
        if cfData["inst"] == 'B2912B':
            self.CF.MD = B2912B()
        elif cfData["inst"] == 'K2636B':
            self.CF.MD = K2636B()
        elif cfData["inst"] == 'K6221':
            self.CF.MD = K6221()
#########################################################################################
############ The main class for the windows #########################################
############## Here is the organization
################################### master######################################################
#################################Main Frame##################################################
################TitleFrame#########ControlFrame##########plotFrame#########LegendFrame################
#############################ConfigFrame##DVIV##MOSFET######################
class MainWindow(): ## an Object oriented frame class
    def __init__(self,master):
        mainFrame=tk.Frame(master)
        mainFrame.pack(padx=10,pady=10,fill='both',expand=1)
        self.titleFrame = tk.Frame(mainFrame)
        lbl_1 = tk.Label(master=self.titleFrame, text="Measurement Tool", font = ('Calibri',14,'bold'))
        lbl_1.pack()
        self.titleFrame.grid(row=0,column=0)
        #self.controlFrame = tk.Frame(mainFrame,highlightbackground="black", highlightthickness=1, width=100, height=100, bd=0)
        lbl_1.grid(row=0,column=0)
        self.PF = plotFrame(mainFrame)
        self.PF.grid(row=1,column = 1)
        self.controlFrame = controlFrame(mainFrame,self.PF)
        self.controlFrame.grid(row=1,column=0)
        self.legendFrame = tk.Frame(mainFrame)
        qButton = tk.Button(master=self.legendFrame,text="Quit",command=self._quit)
        qButton.grid(row = 0,column = 0)
        lbl_mp = tk.Label(master=self.legendFrame, text="")
        lbl_mp.grid(row =0,column = 1)
        self.legendFrame.grid(row=2,column=0)


    def _quit(self):
        root.quit()
        root.destroy()

class Broom:
    def __init__(self):
        try:
            self.rm = visa.ResourceManager()
            self.device_6221 = self.connect_instrument(INSTRUMENT_RESOURCE_STRING_6221, '\r', '\n')
            self.device_2182A = self.connect_instrument(INSTRUMENT_RESOURCE_STRING_2182A, '\r', '\n')
            response_6221 = self.device_6221.query('*IDN?')
            response_2182A = self.device_2182A.query('*IDN?')
            print("6221 ID:", response_6221)
            print("2182A ID:", response_2182A)

        except visa.VisaIOError as e:
            print(f"Error initializing instruments: {e}")
            sys.exit(1)

    
    
    def connect_instrument(self, resource_string, write_termination, read_termination):
        try:
            instrument = self.rm.open_resource(resource_string, write_termination=write_termination, read_termination=read_termination)
            instrument.timeout = 10000  # Set timeout to 10 seconds
            return instrument
        except visa.VisaIOError as e:
            print(f"Error connecting to instrument {resource_string}: {e}")
            sys.exit(1)

    def list_resources(self):
        try:
            resources = self.rm.list_resources()
            print("Available VISA resources:")
            for resource in resources:
                print(resource)
        except Exception as e:
            print(f"Error listing VISA resources: {e}")

    def send_command(self, device, command: str) -> None:
        try:
            if DEBUG_PRINT_COMMANDS:
                print(f"Sending command to {device}: {command}")
            device.write(command)
        except visa.VisaIOError as e:
            print(f"Error sending command '{command}' to {device}: {e}")

    def query_command(self, device, command: str) -> str:
        try:
            if DEBUG_PRINT_COMMANDS:
                print(f"Querying command from {device}: {command}")
            response = device.query(command)
            if DEBUG_PRINT_COMMANDS:
                print(f"Response: {response}")
            return response
        except visa.VisaIOError as e:
            print(f"Error querying command '{command}' from {device}: {e}")
            return ""

    def ping_device(self, device_name):
        try:
            if device_name == "6221":
                device = self.device_6221
                response = self.query_command(device, '*IDN?')
                if response:
                    print(f"6221 is responding: {response}")
                else:
                    print("6221 is not responding.")
            elif device_name == "2182A":
                device = self.device_2182A
                response = self.query_command(device, '*IDN?')
                if response:
                    print(f"2182A is responding: {response}")
                else:
                    print("2182A is not responding.")
            else:
                print(f"Unknown device: {device_name}")
        except Exception as e:
            print(f"Error pinging device {device_name}: {e}")

    def broomrun(self):
        try:
            self.deviceprimer()
            self.armquery()
            self.usercheck()
            self.sweep()
            self.startsweepcheck()
            data = self.read()
            self.save_data(data)
            self.testreset()
        except Exception as e:
            print(f"Error running Broom: {e}")

    def deviceprimer(self):
        try:
            # Abort tests in the other modes
            self.send_command(self.device_6221, ":SOUR:SWE:ABOR")
            self.send_command(self.device_6221, ":SOUR:WAVE:ABOR")
            self.send_command(self.device_6221, "*RST")  # Reset the 6221
            time.sleep(7)  # Wait 7 seconds

            # Query if the 6221 has reset properly
            if self.query_command(self.device_6221, "*OPC?").strip() != "1":
                print("6221 did not reset properly.")
                sys.exit(1)

            self.send_command(self.device_2182A, "*RST")  # Reset the 2182A
            time.sleep(5)  # Wait 5 seconds

            # Query if the 2182A has reset properly
            if self.query_command(self.device_2182A, "*OPC?").strip() != "1":
                print("2182A did not reset properly.")
                sys.exit(1)

            self.send_command(self.device_6221, "pdel:swe ON")  # Set pulse sweep state
            self.send_command(self.device_6221, ":form:elem READ,TST,RNUM,SOUR")  # Set readings to be returned
            time.sleep(1)  # Wait 1 second
            self.send_command(self.device_6221, ":sour:swe:spac LIN")  # Set pulse sweep spacing
            self.send_command(self.device_6221, ":sour:curr:start 0")  # Set pulse sweep start
            self.send_command(self.device_6221, ":sour:curr:stop 0.01")  # Set pulse sweep stop
            self.send_command(self.device_6221, ":sour:curr:poin 11")  # Set pulse count
            self.send_command(self.device_6221, ":sour:del 0.01")  # Set pulse delay
            self.send_command(self.device_6221, ":sour:swe:rang BEST")  # Set sweep range
            self.send_command(self.device_6221, ":sour:pdel:lme 2")  # Set number of low measurements
            self.send_command(self.device_6221, ":sour:curr:comp 100")  # Set pulse compliance
            self.send_command(self.device_2182A, ":sens:volt:rang 10")  # Set voltage measure range
            self.send_command(self.device_6221, "UNIT V")  # Set units
            time.sleep(1)
            self.send_command(self.device_6221, ":sour:swe:arm")  # Arm the pulse sweep
            time.sleep(3)  # Wait 3 seconds
            self.armquery()
        except Exception as e:
            print(f"Error in device primer: {e}")

    def armquery(self):
        try:
            # Query the pulse sweep arm status
            arm_status = self.query_command(self.device_6221, ":sour:swe:arm:stat?")
            print(f"Pulse sweep armed: {arm_status}")
            return arm_status
        except Exception as e:
            print(f"Error querying arm status: {e}")
            return ""

    def sweep(self):
        try:
            self.send_command(self.device_6221, ":init:imm")  # Start the pulse sweep
            print("Pulse sweep initiated.")
            time.sleep(4)  # Wait 4 seconds
        except Exception as e:
            print(f"Error initiating sweep: {e}")

    def get_data_points(self):
        try:
            # Query the number of points in the buffer
            data_points = int(self.query_command(self.device_6221, ":TRAC:POIN:ACT?").strip())
            print(f"Data points available: {data_points}")
            return data_points
        except Exception as e:
            print(f"Error querying data points: {e}")
            return 0

    def read(self):
        try:
            # Read the pulse sweep data
            data_points = self.get_data_points()
            if data_points == 0:
                print("No data points available to read.")
                return ""
            
            data = self.query_command(self.device_6221, f":TRAC:DATA? 1,{data_points}")
            print(data)
            return data
        except Exception as e:
            print(f"Error reading data: {e}")
            return ""

    def save_data(self, data):
        try:
            # Save the data to a CSV file
            filename = "pulsesweepdata.csv"
            with open(filename, "w", newline='') as file:
                writer = csv.writer(file)
                # Assuming the data is a single string of comma-separated values
                rows = data.split(',')
                writer.writerow(["Voltage Reading", "Timestamp", "Source Current"])
                for i in range(0, len(rows), 3):
                    if i + 2 < len(rows):
                        writer.writerow([rows[i], rows[i+1], rows[i+2]])
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data: {e}")

    def startsweepcheck(self):
        try:
            # Check if the pulse sweep is running
            sweep_running = self.query_command(self.device_6221, ":sour:swe:stat?")
            print(f"Pulse sweep running: {sweep_running}")
            return sweep_running
        except Exception as e:
            print(f"Error checking sweep status: {e}")
            return ""

    def usercheck(self):
        # If user decides to abort or continue the Broom
        user_decision = input("Do you want to continue with Broom? (yes/no): ")
        if user_decision.lower() == "no":
            print("Aborting the Broom as per user's request.")
            self.send_command(self.device_6221, ":SOUR:SWE:ABORT")  # Abort the test
            self.testreset()  # Reset the instruments
            sys.exit(1)
        elif user_decision.lower() == "yes":
            print("Resuming Broom.")
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
            self.usercheck()
    
    def testreset(self):
        try:
            self.send_command(self.device_6221, ":SOUR:SWE:ABOR")
            self.send_command(self.device_6221, "*RST")
            time.sleep(3)
            
            # Query if the 6221 has reset properly
            if self.query_command(self.device_6221, "*OPC?").strip() != "1":
                print("6221 did not reset properly.")
                sys.exit(1)

            self.send_command(self.device_2182A, "*RST")
            time.sleep(3)
            
            if self.query_command(self.device_2182A, "*OPC?").strip() != "1":
                print("2182A did not reset properly.")
                sys.exit(1)

            self.query_command(self.device_6221, ":sour:swe:arm:stat?")
            self.query_command(self.device_6221, ":sour:swe:stat?")
            print("Test reset successful.")
        except Exception as e:
            print(f"Error in test reset: {e}")

    def close(self):
        try:
            self.device_6221.close()
            self.device_2182A.close()
            self.rm.close()
            print("Connection closed.")
        except Exception as e:
            print(f"Error closing connection: {e}")

    def parse_and_execute(self):
        parser = argparse.ArgumentParser(description="Broom v1.01")
        parser.add_argument('--testreset', action='store_true', help='Perform a test reset')
        parser.add_argument('--deviceprimer', action='store_true', help='Prime devices for sweep')
        parser.add_argument('--armquery', action='store_true', help='Query the arm status')
        parser.add_argument('--sweep', action='store_true', help='Start the sweep')
        parser.add_argument('--read', action='store_true', help='Read the data')
        parser.add_argument('--save', action='store_true', help='Save the data')
        parser.add_argument('--startsweepcheck', action='store_true', help='Check if the sweep is running')
        parser.add_argument('--usercheck', action='store_true', help='Check if the user wants to continue')
        parser.add_argument('--getdatapoints', action='store_true', help='Get the number of data points')
        parser.add_argument('--ping', nargs='?', const='all', help='Ping devices to check if they are responding')

        args = parser.parse_args()

        try:
            # Using a dictionary to simulate a switch-case block
            actions = {
                "testreset": self.testreset,
                "deviceprimer": self.deviceprimer,
                "armquery": self.armquery,
                "sweep": self.sweep_sequence,
                "read": self.read,
                "save": self.save_sequence,
                "startsweepcheck": self.startsweepcheck,
                "usercheck": self.usercheck,
                "getdatapoints": self.get_data_points,
            }

            if args.ping:
                if args.ping == 'all':
                    self.ping_device("6221")
                    self.ping_device("2182A")
                else:
                    self.ping_device(args.ping)
            else:
                for action, func in actions.items():
                    if getattr(args, action):
                        func()
                        break
        except Exception as e:
            print(f"Error parsing arguments: {e}")
            return None

        return args

    def sweep_sequence(self):
        self.usercheck()
        self.sweep()

    def save_sequence(self):
        data = self.read()
        self.save_data(data)

def main():
    broom = Broom()
    args = broom.parse_and_execute()

    if not args:
        try:
            broom.broomrun()
        finally:
            broom.close()

if __name__ == "__main__":
    main()

#### initiate logging ###########
logging.basicConfig(filename= "logFile.txt", filemode='a',format='%(asctime)s - %(levelname)s -%(message)s',level=logging.INFO)
logging.info('Logging is started')
root = tk.Tk()
window = MainWindow(root)
root.mainloop()
logging.info('Logging ended')