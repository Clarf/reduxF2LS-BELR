import pandas as pd
import matplotlib.pyplot as plt

def wavecal_residuals(filename):
    df = pd.read_csv(filename, sep='\t', header=None, 
                     names=['lambda', 'residual_arc', 'residual_OH'])

    ax = df.plot(kind='scatter', x='lambda', y='residual_arc', 
                 title='Residual on OH lines with arc solution')
    ax.set_xlabel('Wavelength [Angstroms]')
    ax.set_ylabel('Residual [Angstroms]')
    ax.get_figure().savefig('residual_arc.png')

    ax = df.plot(kind='scatter', x='lambda', y='residual_OH',
                 title='Residual on OH lines with OH solution')
    ax.set_xlabel('Wavelength [Angstroms]')
    ax.set_ylabel('Residual [Angstroms]')
    ax.get_figure().savefig('residual_OH.png')


