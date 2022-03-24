"""
Read datas from spetrometer and save them to hdf5file

If enoug time plot them

"""

import sys
import numpy as np
import logging
from multiprocessing import Process
from time import sleep,time
import multiprocessing
import matplotlib.pylab as plt
import numpy as np
from numpy.random import default_rng
rng = np.random.default_rng(12345)
import BWTEK
class Reader(Process):
    def __init__(self, q_array):
        super(Reader, self).__init__()
        self._q_array=q_array

        # # Create figure for plotting
        self.fig = plt.figure()
        self.xs = []
        self.ys = []
        self.wavelength=np.arange(2048)*600/2048+300
        self.spectras = []

        # Axes for ttlin
        self.ax = self.fig.add_subplot(2, 2, (1,2))
        # Axes for spectra
        self.ax1 = self.fig.add_subplot(2, 2, 3)


    def bufferdatas(self, data):
        if not data is None:
            spectra, ti , tf, ttlin=data
            # add datas
            self.xs.append(ti)
            self.ys.append(ttlin)
            self.spectras.append(spectra)

            # limit graph
            max_val=100
            self.xs = self.xs[-max_val:]
            self.ys = self.ys[-max_val:]
            self.spectras = self.spectras[-20:]
            



    def animate(self):
        # Draw x and y lists
        self.ax.clear()
        self.ax.plot(self.xs, self.ys)
        self.ax1.clear()
        self.ax1.plot(self.wavelength,np.array(self.spectras).transpose())
        plt.draw()
        plt.pause(0.001)    

    def run(self):
        self.log = multiprocessing.get_logger()
        self.log.info("Waiting for measurement start")
        # monitor and read loop
        while 1:
            n=self._q_array.qsize()
            if n>0:
                self.log.info(f"{n} items in queue")
            data=self._q_array.get()
            
            if data is None:
                self.log.info(f"empty queue Closing")
                break
            else:
                self.bufferdatas(data)
                sleep(0.008)
            
            if n<2: #if we have time (queue nealy empty) plot datas
                self.animate()
        return


def simulate_datas(ttlin):
        data=(10-2*ttlin)*np.exp(-(np.arange(2048)-850)**2/200**2)+0.1*rng.random(2048)
        sleep(20e-3) #measurement
        return data


if __name__ == "__main__":
    log = multiprocessing.log_to_stderr(logging.INFO)

    # do not work on old python
    q_array = multiprocessing.Queue()
    
    log.info("Creating Processes")
    reader = Reader(q_array)
    reader.start()
    
    log.info("preparing for measurement")
    inst=BWTEK.spectrometer()

    inst.integrationTime(20)
    inst.readEEPROM()
    inst.readConfig()
    log.info(f"connect to {inst.config['COMMON']['model']}")

    log.info("measurement start")
    # Write loop
    i=0
    N=300*100
    p.nice(psutil.REALTIME_PRIORITY_CLASS)
    while i<N:
        ti=time()
        
        ttlin=int(i/13)%2
        #simulate datas
        #data=simulate_datas(ttlin)
        data,ttlin=inst.readSpectrumTTL()
        
        if i%10==0:
            log.info(f"Writing data {i}")
        tf=time()
        q_array.put((data, ti, tf, ttlin))
        i+=1
    
    p.nice(psutil.NORMAL_PRIORITY_CLASS)     
    #send stop to reader    
    q_array.put(None) 

    
    
    logging.info("Stopping")
    reader.join(1)
    reader.terminate()
    inst.close()