"""
Read datas from spetrometer and save them to hdf5file



"""

import sys
import numpy as np
import logging
from multiprocessing import Process
from time import sleep,time
import multiprocessing
import matplotlib.pylab as plt
import numpy as np



class SwmrReader(Process):
    def __init__(self, mpShared,q_array):
        super(SwmrReader, self).__init__()
        self._mpShared=mpShared
        self._q_array=q_array

        # Create figure for plotting
        self.fig = plt.figure()
        self.xs = []
        self.ys = []
        self.wavelength = np.arange(2048)/600+600
        self.spectras = []

        # Axes for ttlin
        self.ax = self.fig.add_subplot(2, 2, (1,2))
        # Axes for spectra
        self.ax1 = self.fig.add_subplot(2, 2, 3)


    def bufferdatas(self, data):
        spectra, ti , tf, ttlin=data
        # add datas
        self.xs.append(ti)
        self.ys.append(ttlin)
        self.spectras.append(spectra)

        # limit graph
        max_val=100
        self.xs = self.xs[-max_val:]
        self.ys = self.ys[-max_val:]
        self.spectras = self.spectras[-10:]




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
        self._mpShared.barrier.wait()
        self.log.info("measurement start: reader")
        try:
            # monitor and read loop
            while 1:
                if  self._mpShared.shutdown_event.is_set():
                    self.log.info(f"Closing after flushing{self._q_array.qsize()} items in queue") 

                if self._q_array.qsize()>0:
                    self.log.info(f"{self._q_array.qsize()} items in queue")    
                    for k in range(self._q_array.qsize()):
                        data=self._q_array.get()
                        self.bufferdatas(data)
                        sleep(0.008)
                    self.animate()
                    
                if self._mpShared.shutdown_event.is_set() and self._q_array.qsize()==0:
                    self.log.info(f"empty que Closing")
                    break
                                              
        except:
            self.log.error("Exception in reader", exc_info=1)
            self._mpShared.shutdown_event.set()            
        finally:
            self.log.info("Closing reader")
            self._q_array.close() 
            # here we close the file
            # self._mpShared.shutdown_event.clear()

class ReadSpectrometer(Process):
    def __init__(self, mpShared,q_array):
        super(ReadSpectrometer, self).__init__()
        self._mpShared=mpShared
        self._q_array=q_array


    def run(self):
        #multiprocessing.log_to_stderr()
        self.log = multiprocessing.get_logger()
        self.log.info("Creating file %s", self._mpShared.fname)
        try:
            self.log.info("preparing for measurement")
            self._mpShared.barrier.wait()
            self.log.info("measurement start")
            # Write loop
            i=0
            while i<100:
                ti=time()
                sleep(20e-3)
                ttlin=i%5
                data=(1000+ttlin)*np.exp(-(np.arange(2048)-850)**2/200**2)
                
                
                if i%10==0:
                    self.log.info(f"Writing data {i}")
                tf=time()
                self._q_array.put((data, ti, tf, ttlin))
                self._mpShared.event.set()
                if self._mpShared.shutdown_event.is_set():
                    break
                i+=1
        except KeyboardInterrupt:
            pass        
        except:
            self.log.error("Exception in writer", exc_info=1)          
        finally:
            self.log.info("Closing ReadSpectrometer")

import sys, signal
def signal_handler(signal, frame):
    print("\nprogram exiting gracefully")
    mpShared.shutdown_event.set()




if __name__ == "__main__":
    logger = multiprocessing.log_to_stderr(logging.INFO)
    signal.signal(signal.SIGINT, signal_handler)
    dsetname = 'data'
    if len(sys.argv) > 1:
        fname = sys.argv[1]
    if len(sys.argv) > 2:
        dsetname = sys.argv[2]


    with multiprocessing.Manager() as Manager:
        mpShared=Manager.Namespace()
        timeout=1

        # events
        mpShared.event = Manager.Event()
        mpShared.barrier = Manager.Barrier(2)
        mpShared.shutdown_event = Manager.Event()
        mpShared.event_stop = Manager.Event()

        # do not work on old python
        #mpShared.q_array = Manager.Queue()
        q_array = multiprocessing.Queue()


        #common datas
        mpShared.fname = 'swmrmp2.h5'
        mpShared.timeout= 1
        mpShared.meas_idx= 0
        

        logger.info("Creating Processes")
        reader = SwmrReader(mpShared,q_array )
        writer = ReadSpectrometer(mpShared,q_array)
        
        logging.info("Starting reader")
        reader.start()
        logging.info("Starting writer")
        writer.start()
        logging.info("waiting for close")
        
        while not mpShared.shutdown_event.is_set():
            sleep(1)
         
        
        logging.info("reader closed")
        q_array.close()
        writer.join()
        reader.join()
        writer.terminate()

    