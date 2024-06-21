import numpy as np
import pandas as pd
import os
import glob
import matplotlib.pyplot as plt

def plot_reference_dark(path, dark_filename, reference_filename):
    """
    Plots the dark and reference (Sp + Sn)/2 in function of the wavelength.
    Also return the dataframes contained on such files, respectively.
    """
    
    dark_path = glob.glob(path + '*' + dark_filename + '*')[0]
    reference_path = glob.glob(path + '*' + reference_filename + '*')[0]
    
    dark = pd.read_csv(dark_path, sep=';', decimal=',', comment='#')
    reference = pd.read_csv(reference_path, sep=';', decimal=',', comment='#')
    
    plt.figure(figsize=(14, 14))
    plt.subplot(3,1,1)
    plt.plot(dark['Wavelength'], (reference['Sp mean']+reference['Sn mean'])/2, label='(Sp + Sn)/2')
    plt.xlabel(r'$\lambda$')
    plt.ylabel(r'Count $\approx I_0 $')
    plt.title('Reference')
    plt.grid()
    plt.legend()
    
    plt.subplot(3,1,2)
    plt.plot(dark['Wavelength'], (dark['Sp mean']+dark['Sn mean'])/2, label='(Sp + Sn)/2')
    plt.xlabel(r'$\lambda$')
    plt.ylabel('Count')
    plt.title('Dark')
    plt.grid()
    plt.legend()

    plt.subplot(3,1,3)
    plt.plot(dark['Wavelength'], (reference['Sp mean']+reference['Sn mean'])/2-(dark['Sp mean']+dark['Sn mean'])/2, label='(Sp + Sn)/2')
    plt.xlabel(r'$\lambda$')
    plt.ylabel('Count')
    plt.title('Reference - Dark')
    plt.grid()
    plt.legend()
    
    plt.show()

    return dark, reference

def compute_absorbance(path, dark, reference, signal_filename):

    signal_path = glob.glob(path + signal_filename + '*')[0]
    signal = pd.read_csv(signal_path, sep=';', decimal=',', comment='#')

    A = -0.5 * (np.log10(signal['Sp mean']-dark['Sp mean'])+np.log10(signal['Sn mean']-dark['Sp mean'])-2*np.log10(reference['Sp mean']-dark['Sp mean']))
    dA = -0.5*( np.log10(signal['Sp mean']-dark['Sp mean']) - np.log10(signal['Sn mean']-dark['Sp mean']) )

    plt.figure(figsize=(14, 14))
    plt.subplot(4,1,1)
    plt.plot(signal['Wavelength'], (signal['Sp mean']+signal['Sn mean'])/2, label='(Sp + Sn)/2')
    plt.xlabel(r'$\lambda$')
    plt.ylabel(r'Count')
    plt.title('Signal')
    plt.grid()
    plt.legend()
    
    plt.subplot(4,1,2)
    plt.plot(signal['Wavelength'], A, label='A')
    plt.xlabel(r'$\lambda$')
    plt.grid()
    plt.legend()

    plt.subplot(4,1,3)
    plt.plot(signal['Wavelength'], dA, label=r'$\delta A$')
    plt.xlabel(r'$\lambda$')
    plt.grid()
    plt.legend()

    plt.subplot(4,1,4)
    plt.plot(signal['Wavelength'], dA/A, label=r'$\delta A /A$')
    plt.xlabel(r'$\lambda$')
    plt.grid()
    plt.legend()

    plt.show()
