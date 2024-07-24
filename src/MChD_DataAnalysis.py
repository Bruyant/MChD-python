# Libraries Import
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
import os
from Routines import *

# Inputs Definition
dark_filename = '2024-06-13_15-30-27'
signal_filename = 'MChD_2024-07-01_14-19'
reference_filename = 'MChD_2024-06-13_15-33-18'

# Computation code
path = os.path.expanduser('~').replace('\\', '/') + r'/Documents/MChD_Data/'
print(f'Detected storage path: {path}')
dark, reference = plot_reference_dark(path, dark_filename, reference_filename)
signal = compute_absorbance(path, dark, reference, signal_filename)
plt.show()
