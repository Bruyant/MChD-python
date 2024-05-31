import sys
from pymeasure.display.Qt import QtWidgets
from pymeasure.display.windows.managed_dock_window import ManagedDockWindow
from MChD_Procedures import SpectrometerProcedure


class MainWindow(ManagedDockWindow):
    # Docked plots are started, the layout can be saved in a file that will be load at startup if it exists.
    parameters_list = ['averages_pairs', 'spec_int_time', 'control_voltage', 'mag_inertia', 'comment']

    def __init__(self):
        super().__init__(
            procedure_class=SpectrometerProcedure,
            inputs=self.parameters_list,
            displays=self.parameters_list,
            x_axis=['Wavelength'],
            y_axis=['Sp+Sn /2', 'Sp-Sn /2', 'Sp+Sn /2 mean', 'Sp-Sn /2 mean'],
            sequencer=True,  # Added line
            # sequencer_inputs = ['iterations', 'delay', 'seed'],  # Added line
            # sequence_file = "gui_sequencer_example_sequence.txt",  # Added line, optional

            inputs_in_scrollarea=True,
            # hide_groups=True # choose between hiding the groups (True) and disabling / graying-out the groups (False)
        )
        self.setWindowTitle('GUI for MChD')

        # TODO: Adapt structure
        self.filename = r'default_filename_delay{Delay Time:4f}s'  # Sets default filename
        self.directory = r'C:/Path/to/default/directory'  # Sets default directory
        self.store_measurement = False  # Controls the 'Save data' toggle
        self.file_input.extensions = ["csv", "txt", "data"]  # Sets recognized extensions, first is the default
        self.file_input.filename_fixed = False  # Controls whether the filename-field is frozen (but still displayed)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
