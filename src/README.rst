General Usage:
Upon cloning the directory, use the following commands to install all the dependencies and be ready to use the software:

cd <your_storage>/MChD-python/src
conda env create -f environment.yml
conda activate MChD


On Windows 10 32bit:
The compatible Anaconda installs python 3.7 which is not compatible with the software dependencies.
Thus, the environment management won't be applied.

Instead the following requirements were installed:
	* PyCharm: 2018.3.7
	* NiDaqMx 20.1
	* Python 3.8.10
Then the needed python libraries to install are: matplotlib, pymeasure, PyQt5, nidaqmx.
