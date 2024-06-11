import ctypes as ct
import time
from time import sleep

from datetime import datetime

from numpy.ctypeslib import as_array
from numpy.polynomial import Polynomial
from numpy.polynomial.polynomial import polyval

import matplotlib.pyplot as plt

from contextlib import AbstractContextManager
import configparser
import numpy as np

class GlacierX(AbstractContextManager):
    dll="C:/BWTEK/BWSpec4/BWTEKUSB.dll"
    dll=(r"C:\Users\lorenco\Documents\GitHub\MChD-python\bwtek\BWTEKUSB.dll")
    def __init__(self,channel=0,pixels=2048):
        """
        BWTEK USB dll wrapper
        Init the lib and connect to the first spectrometer
        TODO : support mutiple spectrometers
        """
        #Open dll
        self.lib = ct.windll.LoadLibrary(self.dll)
        
        #define returns types of dll functions
        self.lib.InitDevices.restype = ct.c_bool
        self.lib.bwtekSetTimeUSB.restype = ct.c_long
        
        
        #defines parameters
        self.channel = ct.c_int(int(channel))
        
        #spectrometers params
        self.nTriggerMode=ct.c_int(0)
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
        self.lib.GetUSBType(ct.byref(nUSBType), self.channel)
        return nUSBType.value

    def readEEPROM(self,filename="param.txt"):
        """
        Read parameters from eprom
        """
        filename = ct.create_string_buffer(str.encode(filename))
        self.lib.bwtekReadEEPROMUSB(filename,self.channel)
        
    def readConfig(self,filename="param.txt"):
        """
        Read parameters from ini file 
        
        """
        config = configparser.ConfigParser()
        config.read('param.txt')
        #configdict={s:dict(config.items(s)) for s in config.sections()}
        self.config=config
        
        self.pixel_num=int(self.config['COMMON']['pixel_num'])
        
        return config
    
    def getInterpolate(self):
        """
        Read tha parametyers polynomial
        set self.wavelengths : array in nm of wavelegnth for each pixels
        Return an interpolating function
        """
        a,b = [0,0,0,0],[0,0,0,0]
        for i in range(4):
            a[i]=float(self.config['COMMON']['coefs_a'+str(i)])
           #b[i]=float(self.config['COMMON']['coefs_b'+str(i)])
        
        self.wavelengths = Polynomial(a).linspace(n=self.pixel_num, domain=[0,self.pixel_num])[1]
        
        #pb = np.polynomial.Polynomial(b)
        return lambda x:polyval(x,a)
    
    def interpolation(self):
        calib=dict(self.config['CALIBRATION'])
        x,y=[],[]
        for point in calib:
            a,b=[float(x) for x in calib[point].split(';')]
            x.append(a)
            y.append(b)
        return x,y

    def shutdown(self):
        self.lib.CloseDevices()

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
        self.channel = ct.c_int(int(0))
        self.pArray = (ct.c_ushort * 2048)()
        self.nTriggerMode = ct.c_int(0)

        self.lib.bwtekDataReadUSB(self.nTriggerMode,
                                  ct.byref(self.pArray), self.channel)
        return np.float32(as_array(self.pArray))
    
    def integrationTime(self, Itime):
        """
        Itime for BTC112E: 5 – 65535ms in milliseconds

        """
        Itime = ct.c_long(int(Itime))
        return self.lib.bwtekSetTimeUSB(Itime, self.channel)
        
    def readSpectrumTTL(self):
        """
        read the spectrum and TTL input value before and after spectrum
        return: 
            - numpy array sharing the memory of the spectrum,
            - summ of TTL input before and after
        """
        ttl_in=self.lib.bwtekGetExtStatus(self.channel)
        self.lib.bwtekDataReadUSB(self.nTriggerMode,
                                  ct.byref(self.pArray),self.channel)
        ttl_in+=self.lib.bwtekGetExtStatus(self.channel)
        return as_array(self.pArray),ttl_in       
        
    def storeSpectrums(fname,res,ttlin,tstamps):
        """
        read the spectrum and TTL value before and after
        return: numpy array sharing the memory,summ of TTL input before and after
        """
        with h5py.File(fname, "w") as hf:
            g=hf.create_group('Scan')
            g.create_dataset("Spectrums", data=res,dtype='u2',compression="gzip")
            g.create_dataset("TTLinput", data=ttlin,dtype='i1',compression="gzip")
            g.attrs["Timestamps"]=[str(tstamp) for tstamp in tstamps]  

    def readResult(self, averages, smooth_type=0, smooth_value=0):
        """
                This function is for reading out data from the detector then applying some data processing
                return: numpy array sharing the memory

        smooth_type: 0 for no smoothing function
                     1 for FFT smoothing
                     2 for Savitzky-Golay smoothing
                     3 for Boxcar smoothing.

        smooth_value: When using FFT smoothing (nTypeSmoothing=1), this parameter indicates the percentage of cutoff
                      frequency. The nValueSmoothing should be 0 to 100.
                      When using Savitzky-Golay smoothing (nTypeSmoothing=2), The nValueSmoothing should be 2 to 5.

        """
        self.channel = ct.c_int(int(0))
        self.pArray = (ct.c_ushort * 2048)()
        self.nTriggerMode = ct.c_int(0)

        self.lib.bwtekReadResultUSB(self.nTriggerMode, averages, smooth_type, smooth_value,
                                  ct.byref(self.pArray), self.channel)
        return np.float32(as_array(self.pArray))
        
if __name__ == '__main__':
    with GlacierX() as inst:
        inst.readEEPROM()
        print('EEPROM read into file')
        inst.readConfig()
        inttime = 5
        print(inst.integrationTime(inttime))
        print(f'integration time changed to {inttime}')
        inst.getInterpolate()
        spectrum = inst.readSpectrum()

        spectrum2 = inst.readSpectrum()
    plt.plot(inst.wavelengths, spectrum)
    plt.plot(inst.wavelengths, spectrum2)
    plt.show()
