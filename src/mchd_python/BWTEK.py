import ctypes as ct
from time import sleep

from datetime import datetime

from numpy.ctypeslib import as_array
from numpy.polynomial import Polynomial
from numpy.polynomial.polynomial import polyval

import matplotlib.pyplot as plt

from contextlib import AbstractContextManager
import configparser


class spectrometer(AbstractContextManager):
    "C:/BWTEK/BWSpec4/BWTEKUSB.dll"
    def __init__(self,channel=0,pixels=2048):
        """
        BWTEK USB dll wrapper
        Init the lib and connect to the first spectrometer
        TODO : support mutiple spectrometers
        """
        #Open dll
        self.lib = ct.windll.LoadLibrary("C:/BWTEK/BWSpec4/BWTEKUSB.dll")
        
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
        self.lib.GetUSBType(ct.byref(nUSBType),self.channel)
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
        
        
if __name__ == '__main__':
    with spectrometer() as inst:
        inst.readEEPROM("atest.dat")
        print('EEPROM read into file')
        inttime=20
        print(inst.integrationTime(inttime))
        print(f'integration time changed to {inttime}')
        plt.plot(inst.readSpectrum())
        plt.show()