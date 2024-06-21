import sys
from pymeasure.display.Qt import QtWidgets
from pymeasure.display.windows.managed_dock_window import ManagedDockWindow
from MChD_Procedures import SpectrometerProcedure
from pymeasure.experiment import unique_filename, Results
from datetime import datetime
import pandas as pd
import os


class MainWindow(ManagedDockWindow):
    # Docked plots are started, the layout can be saved in a file that will be load at startup if it exists.
    parameters_list = ['field_pairs', 'spec_int_time', 'spec_averages', 'control_voltage', 'magnet_switch', 'comment']

    def __init__(self):
        super().__init__(
            procedure_class=SpectrometerProcedure,
            inputs=self.parameters_list, 
            displays=self.parameters_list,
            x_axis=['Wavelength'],
            y_axis=['Sp+Sn /2', 'Sp+Sn /2 mean', 'Sp-Sn /2 mean'],
            sequencer=False,  # Added line
            enable_file_input=True,
            # sequencer_inputs = ['iterations', 'delay', 'seed'],  # Added line
            # sequence_file = "gui_sequencer_example_sequence.txt",  # Added line, optional

            inputs_in_scrollarea=True,
            # hide_groups=True # choose between hiding the groups (True) and disabling / graying-out the groups (False)
        )
        self.setWindowTitle('GUI for MChD')
        self.filename = r"MChD_"  # Sets default filename
        self.directory = os.path.expanduser('~').replace('\\', '/') + r'/Documents/MChD_Data'  # Sets default directory
        # self.store_measurement = False  # Controls the 'Save data' toggle
        # self.file_input.extensions = ["csv", "txt", "data"]  # Sets recognized extensions, first is the default
        self.file_input.filename_fixed = True  # Controls whether the filename-field is frozen (but still displayed)

    def queue(self):
        self.f = unique_filename(self.directory, prefix=self.filename, datetimeformat='%Y-%m-%d_%H-%M-%S',
                                 index=False, ext='dat')  # from pymeasure.experimentD

        procedure = self.make_procedure()  # Procedure class was passed at construction
        results = Results(procedure, self.f)
        experiment = self.new_experiment(results)

        self.manager.queue(experiment)

    def abort(self):
        super().abort()
        self.save_only_last()

    def finished(self, experiment):
        super().finished(experiment)
        self.save_only_last()

    def save_only_last(self):
        # Get Metadata
        l = []
        with open(self.f) as f:
            for line in f.readlines():
                if line[0] == '#':
                    l.append(line)

        # Get data
        data = pd.read_csv(self.f, comment='#', header=0)

        # Filter for last pair and selected columns
        df = data[data['Pair'] == max(data['Pair'])].loc[:, ['Wavelength', 'Sp mean', 'Sn mean']]

        os.remove(self.f)  # Uncomment to delete the complete file and only save the Sigma and Delta mean data

        # Save Metadata
        with open(self.f + '_filtered', 'a') as f:
            for line in l:
                f.write(line)
        with open(self.f + '_filtered', 'ab') as f:
            df.to_csv(f, header=df.columns, index=False, sep=';', decimal=',')


if __name__ == "__main__":

    ###
    # Monkey Patch
    from pymeasure.display.curves import ResultsCurve

    def patched_update_data(self):
        """Updates the data by polling the results"""
        if self.force_reload:
            self.results.reload()
        data = self.results.data  # get the current snapshot

        # Set x-y data
        dfx = data[self.x].tail(2048).tolist()
        dfy = data[self.y].tail(2048).tolist()
        self.setData(dfx, dfy)

    ResultsCurve.update_data = patched_update_data
    ###

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
