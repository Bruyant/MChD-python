#
# This file is part of Python for Magneto-Chiral Dichroism (MChD) package
# (see https://github.com/Bruyant/MChD-python).
#
# Copyright(c) 2014-2024 Nicolas Bruyant & Nuno Prata
# and Centre National de la Recherche Scientifique
# see AUTHORS.rst
#
# Licensed under GPL-3.0-or-later - see LICENSE.rst#

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
