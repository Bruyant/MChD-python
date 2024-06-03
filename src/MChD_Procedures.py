import tempfile
import random
import time
from time import sleep
from pymeasure.log import console_log
from pymeasure.experiment import Procedure, Results
from pymeasure.experiment import IntegerParameter, FloatParameter, Parameter, BooleanParameter

import numpy as np
from datetime import datetime, timedelta

import logging, traceback
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())
log.setLevel("DEBUG")

import matplotlib.pyplot as plt
# Instruments
from BWTEK import GlacierX
from NationalInstruments import DAQ_6001


class SpectrometerProcedure(Procedure):
    # Consider a group_by or group_condition arguments.
    averages_pairs = IntegerParameter('Field Averages/Pairs', default=5)
    spec_int_time = FloatParameter('Spectrometer Integration Time', units='ms', default=5)
    spec_n_averages = IntegerParameter('Spectrometer Averages', default=5)  # TODO: implement it to spectrometer
    control_voltage = FloatParameter('Control Voltage Amplitude', units='V', default=10)

    mag_inertia = FloatParameter('Magnet Inertia Time', units='s', default=0.5)

    comment = Parameter('Comment', default='No Comment')

    DATA_COLUMNS = ['Pair', 'Wavelength', 'max_SUM', 'Sp', 'Sn', 'Sp mean', 'Sn mean', 'Sp+Sn /2', 'Sp-Sn /2',
                    'Sp+Sn /2 mean', 'Sp-Sn /2 mean']

    # Parameters Initialisation
    progress = 0
    pair = 0
    NIDAQ_points = 1000
    NIDAQ_Fs = 1000

    Sp_all = []
    Sn_all = []

    def startup(self):
        self.x_increase = np.linspace(-np.pi / 2, np.pi / 2, self.NIDAQ_points)
        self.x_decrease = np.linspace(np.pi / 2, 3 / 2 * np.pi, self.NIDAQ_points)

        self.sine_increase = self.control_voltage * np.sin(self.x_increase)
        self.sine_decrease = self.control_voltage * np.sin(self.x_decrease)
        self.sine_ini_increase = self.sine_increase / 2 + self.control_voltage / 2
        self.sine_end_increase = self.sine_increase / 2 - self.control_voltage / 2

        log.info("Connecting and configuring the instruments")

        # Connecting the Spectrometer
        log.info("Connecting Spectrometer GlacierX ...")
        try:
            self.spectrometer = GlacierX()
            self.spectrometer.readConfig()
            self.spectrometer.integrationTime(self.spec_int_time)
            self.spectrometer.getInterpolate()
        except:
            log.error(traceback.format_exc())
            log.error("Spectrometer not connected !")

        # Connecting the NIDAQ 6001
        log.info("Connecting NIDAQ 6001 ...")
        try:
            self.NIDAQ = DAQ_6001()
            self.NIDAQ.set_hardware_timing(self.NIDAQ_Fs)
            # Start
            log.info("Setting the first sine increase on field")
            self.NIDAQ.set_voltage_points(self.sine_ini_increase)
            log.info("First sine increase on field finished")
            time.sleep(self.mag_inertia)
        except:
            log.error(traceback.format_exc())
            log.error("NIDAQ 6001 not connected !")

    def execute(self):

        # On Positive Edge
        Sp = self.spectrometer.readSpectrum()
        self.Sp_all.append(Sp)
        self.progress += 1
        self.emit('progress', 100 * self.progress / (self.averages_pairs * 2))


        # NEGATIVE EDGE
        log.info("Setting the sine decrease on field")
        self.NIDAQ.set_voltage_points(self.sine_decrease)
        log.info("Sine decrease on field finished")
        time.sleep(self.mag_inertia)
        Sn = self.spectrometer.readSpectrum()
        self.Sn_all.append(Sn)
        self.progress += 1
        self.pair += 1

        # Emit data
        self.send_data(Sp, Sn)
        self.emit('progress', 100 * self.progress / (self.averages_pairs * 2))

        for pair in range(1, self.averages_pairs):  # if averages_pairs = 1, the for loop is skipped
            if self.should_stop():
                log.warning("Caught the stop flag in the procedure")
                break

            # POSITIVE EDGE
            log.info(f"Loop {pair}: Setting the sine increase on field")
            self.NIDAQ.set_voltage_points(self.sine_increase)
            log.info(f"Loop {pair}: Sine increase on field finished")
            time.sleep(self.mag_inertia)
            Sp = self.spectrometer.readSpectrum()
            self.Sp_all.append(Sp)
            self.progress += 1
            self.emit('progress', 100 * self.progress / (self.averages_pairs * 2))

            if self.should_stop():
                log.warning("Caught the stop flag in the procedure")
                break

            # NEGATIVE EDGE
            log.info(f"Loop {pair}: Setting the sine decrease on field")
            self.NIDAQ.set_voltage_points(self.sine_decrease)
            log.info(f"Loop {pair}: Sine decrease on field finished")
            time.sleep(self.mag_inertia)
            Sn = self.spectrometer.readSpectrum()
            self.Sn_all.append(Sn)
            self.progress += 1
            self.pair += 1

            # Emit data
            self.send_data(Sp, Sn)
            self.emit('progress', 100 * self.progress / (self.averages_pairs * 2))


        self.send_means(self.Sp_all, self.Sn_all)

    def send_means(self, Sp_all, Sn_all):
        """

        Args:
            Sp_all: array containing the different arrays corresponding at each spectrum for each positive field.
            Sn_all: array containing the different arrays corresponding at each spectrum for each negative field.

        Emits the Mean of Positive and Negative field spectrums respective to the wavelength.
        It also emits the mean of Sigma ((Sp + Sn )/2) and Delta ((Sp - Sn )/2) spectrums respective to the wavelength.

        """
        Sp_all = np.array(Sp_all)
        Sn_all = np.array(Sn_all)
        spectrum_x = self.spectrometer.wavelengths

        for i in range(len(spectrum_x)):  # TODO: ADAPT to have multiple plots at once, the whole vector
            data = {
                'Wavelength': spectrum_x[i],
                'Sp mean': np.mean(Sp_all, axis=0)[i],
                'Sn mean': np.mean(Sn_all, axis=0)[i],
                'Sp+Sn /2 mean': np.mean((Sp_all + Sn_all)/2, axis=0)[i],
                'Sp-Sn /2 mean': np.mean((Sp_all - Sn_all)/2, axis=0)[i]
            }
            self.emit('results', data)

    def get_estimates(self, sequence_length=None, sequence=None):
        """
        Args:
            sequence_length:
            sequence:

        Returns:
            The displayable structure that contains the estimated time, size, length... of the experiment.
        """

        # TODO: take into account the sequence
        setpoint_reach = self.NIDAQ_points/self.NIDAQ_Fs  # in seconds
        t_meas_spectometer = self.spec_int_time * 1e-3 * self.spec_n_averages  # in seconds

        duration = (setpoint_reach + self.mag_inertia) * (2 * self.averages_pairs + 1) + 2 * t_meas_spectometer * self.averages_pairs

        estimates = [
            ("Duration", "%d s" % int(duration)),
            # ("Number of lines", "%d" % int(self.iterations)),
            # ("Sequence length", str(sequence_length)),
            ('Measurement finished at', str(datetime.now() + timedelta(seconds=duration))),
        ]

        return estimates  # duration

    def send_data(self, Sp, Sn):
        """
        Emit the Sigma ((Sp + Sn )/2) and Delta ((Sp - Sn )/2) Spectrums  at the respective wavelength and pair number.
        """

        spectrum_x = self.spectrometer.wavelengths

        log.debug("Emitting results...")

        if np.max(Sp) > 65000 or max(Sn) > 65000:
            log.warning("Spectrum is possibly saturated !")

        for i in range(len(Sp)):  # TODO: ADAPT to have multiple plots at once, the whole vector
            p = Sp[i]
            n = Sn[i]
            data = {
                'Pair': self.pair,
                'Wavelength': spectrum_x[i],
                'Sp': Sp,
                'Sn': n,
                'Sp+Sn /2':  (p+n) / 2,
                'Sp-Sn /2':  (p-n) / 2,
                'max_SUM': np.max((Sp + Sn)/2)
            }
            self.emit('results', data)
        log.debug("Results emitted...")

    def shutdown(self):
        try:
            self.spectrometer.shutdown()
            del self.spectrometer
        except AttributeError:
            pass

        try:
            log.info("Setting the end sine increase on field")
            self.NIDAQ.set_voltage_points(self.sine_end_increase)
            log.info("End sine increase on field finished")
            time.sleep(self.mag_inertia)
            self.NIDAQ.shutdown()
            del self.NIDAQ
        except AttributeError:
            pass


if __name__ == "__main__":
    from pymeasure.log import console_log
    from pymeasure.experiment import Results, Worker

    console_log(log)

    log.info("Constructing an the Procedure")
    procedure = SpectrometerProcedure()

    procedure.iterations = 1

    data_filename = 'test.csv'
    log.info("Constructing the Results with a data file: %s" % data_filename)
    results = Results(procedure, data_filename)

    log.info("Constructing the Worker")
    worker = Worker(results)
    worker.start()

    log.info("Started the Worker")
    log.info("Procedure status : {}")
    worker.join(timeout=3600)  # wait at most 1 hr (3600 sec)
    log.info("Finished the measurement")
