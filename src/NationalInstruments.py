import time
import nidaqmx.system
import numpy as np


class DAQ_6001(object):
    """
    DAQ 6001 for MChD experiment
    """

    def __init__(self, resourceName="Dev1", **kwargs):
        self.task = nidaqmx.Task()
        self.task.ao_channels.add_ao_voltage_chan(resourceName + '/ao0', max_val=10, min_val=-10)

    def set_voltage_points(self, points):
        # TODO: adapt description
        """
        Change setpoint for scanning coil
        """

        self.task.write(points, auto_start=True)
        self.task.wait_until_done()
        self.task.stop()

    def set_hardware_timing(self, frequency):
        """
        Sets the sampling rate in samples per second as only 1 channel is used.
        """
        self.task.timing.cfg_samp_clk_timing(frequency)

    def shutdown(self):
        self.set_voltage_points([0, 0])
        self.task.stop()
        time.sleep(0.2)
        self.task.close()
        time.sleep(0.2)


if __name__ == '__main__':
    # import logging, traceback
    #
    # log = logging.getLogger(__name__)
    # log.addHandler(logging.NullHandler())
    # from pymeasure.log import console_log
    #
    # console_log(log)
    # e = DAQ_6001()
    #
    # time.sleep(2)
    #
    # e.set_setpoint(1)
    #
    # time.sleep(10)
    #
    # e.shutdown()

    # with nidaqmx.Task() as task:
    #     task.ao_channels.add_ao_voltage_chan("Dev1/ao0")
    #
    #     #task.timing.cfg_samp_clk_timing(1000)
    #
    #     A = -10
    #     N_points = 100000
    #     points = A * np.sin(np.linspace(0, np.pi/2, N_points))
    #     print("1 Channel N Samples Write: ")
    #     print(task.write(points, auto_start=True))
    #     task.wait_until_done()
    #
    #     task.stop()
    #     time.sleep(10)
    #     task.write([0], auto_start=True)
    #     task.wait_until_done()
    #     task.stop()

    import numpy as np
    import matplotlib.pyplot as plt

    ### PROCEDURE TEST
    NIDAQ_points = 1000
    control_voltage = 10
    pairs = 3

    x_increase = np.linspace(-np.pi / 2, np.pi / 2, NIDAQ_points)
    x_decrease = np.linspace(np.pi / 2, 3 / 2 * np.pi, NIDAQ_points)

    sine_increase = control_voltage * np.sin(x_increase)
    sine_decrease = control_voltage * np.sin(x_decrease)

    sine_ini_increase = sine_increase / 2 + control_voltage / 2
    sine_end_increase = sine_increase / 2 - control_voltage / 2

    test_procedure = np.hstack([sine_ini_increase, sine_decrease,  np.tile(np.hstack([sine_increase, sine_decrease]), pairs-1), sine_end_increase])
    ###

    plt.figure()
    plt.plot(test_procedure)
    plt.grid()
    plt.show()

