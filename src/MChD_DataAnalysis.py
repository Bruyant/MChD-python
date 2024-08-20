# Libraries Import
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
import os
from Routines import *

# Inputs Definition
dark_filename = 'MChD_2024-07-12_10-37-51'
signal_filename = 'MChD_2024-07-12_10-58-59'
reference_filename = 'MChD_2024-07-12_11-01-34'

# Computation code
path = os.path.expanduser('~').replace('\\', '/') + r'/Documents/MChD_Data/'
print(f'Detected storage path: {path}')
dark, reference = plot_reference_dark(path, dark_filename, reference_filename)
signal = compute_absorbance(path, dark, reference, signal_filename)
plt.show()
