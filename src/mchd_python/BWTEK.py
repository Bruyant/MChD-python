import ctypes as ct
from time import sleep

from datetime import datetime

from numpy.ctypeslib import as_array

import matplotlib.pyplot as plt

from contextlib import AbstractContextManager



class spectrometer(AbstractContextManager):
    "./bwtek/BWTEKUSB.dll"
    def __init__(self,channel=0,pixels=2048):
        """
        BWTEK USB dll wrapper
        Init the lib and connect to the first spectrometer
        TODO : support mutiple spectrometers
        """
        #Open dll
        self.lib = ct.windll.LoadLibrary("./bwtek/BWTEKUSB.dll")
        
        #define returns types of dll functions
        self.lib.InitDevices.restype = ct.c_bool
        self.lib.bwtekSetTimeUSB.restype = ct.c_long
        
        
        #defines parameters
        self.nTriggerMode=ct.c_int(0)
        self.channel = ct.c_int(int(channel))
        self.nPixelNo = ct.c_int(pixels)
        
        #prams for USB communicatin
        self.nTiming = ct.c_int(1)
        self.nInputMode = ct.c_int(1)
        
        # defines buffers
        self.dVoltage = ct.c_double()
        self.nValue= ct.c_int32()
        
        #Spectrum buffer
        self.pArray=(ct.c_ushort*pixels)()

        self.lib.InitDevices()
        devcount=self.lib.GetDeviceCount()
        if devcount<1:
            raise ConnectionRefusedError

        retUSB=self.lib.bwtekTestUSB(self.nTiming,self.nPixelNo,
                                     self.nInputMode,0,None)
        print(f"Found {devcount} spectrometers , initialized {retUSB}")


    
    def GetUsbType(self):
        """
        Get USB type 
        Return:  1,2,3
        """
        nUSBType = ct.c_int(1)
        self.lib.GetUSBType(ct.byref(nUSBType),self.channel)
        return nUSBType.value

    def readEEPROM(self,filename="param.txt"):
        """
        Read parameters from eprom
        TODO store dict inthe object
        """
        filename = ct.create_string_buffer(str.encode(filename))
        self.lib.bwtekReadEEPROMUSB(filename,self.channel)
        

    
    def __exit__(self,exc_type, exc_value, traceback):
        self.lib.CloseDevices()
    
    def __enter__(self):
        #to use context manager
        return self
        
    def readAnalog(self):
        """
        Read analog voltage on supported spectrometer (untested)
        """
        self.lib.bwtekGetAnalogIn(0,ct.byref(self.nValue), 
                                  ct.byref(self.dVoltage),self.channel)
        return self.dVoltage.value
    
    def readSpectrum(self):
        """
        read the spectrum
        return: numpy array sharing the memory
        """
        self.lib.bwtekDataReadUSB(self.nTriggerMode,
                                  ct.byref(self.pArray),self.channel)
        return as_array(self.pArray)
    
    def integrationTime(self, Itime):
        Itime = ct.c_long(int(Itime))  # Time in microseconds
        return self.lib.bwtekSetTimeUSB(Itime, self.channel)
        
    def readSpectrumTTL(self):
        """
        read the spectrum and TTL value before and after
        return: numpy array sharing the memory,summ of TTL input before and after
        """
        a=self.lib.bwtekGetExtStatus(self.channel)
        self.lib.bwtekDataReadUSB(self.nTriggerMode,
                                  ct.byref(self.pArray),self.channel)
        a+=self.lib.bwtekGetExtStatus(self.channel)
        return as_array(self.pArray),a        
        
        
        
if __name__ == '__main__':
    with spectrometer() as inst:
        #inst.readEEPROM("atest.dat")
        #print('EEPROM read')
        #print('type usb',inst.GetUsbType())
        inttime=20
        print(inst.integrationTime(inttime))
        print(f'integration time changed to {inttime}')
        plt.plot(inst.readSpectrum())
        plt.show()