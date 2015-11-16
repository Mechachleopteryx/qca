#!/usr/bin/python3

'''
Here is an example of how to load in and extract QECA simulation results.
The entire set of python files is available at github.com/lhillber/qca.
'''

import fio as io
import numpy as np
from scipy.ndimage import zoom
import scipy.fftpack as spf
import states as ss
import plotting as pt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter

# import results from the file path/name
results = io.read_results( 
        fname
        ='/home/lhillber/documents/qca/output/sweep_block/data/blockH_R102_ICqt90_P1_L13_tmax70.res' )

params = results['meta']['params']
       
# reform single site density matricies with the real and imaginary parts
sd_list = results['sdr'] + 1j*results['sdi'] 

# grab the time series of mutual information networks
mi = results['mi']

# grab the time series of entropy of all bi-partite cuts
ec = results['ec']

# grab the time series of inverse participation ratio 
ipr = results['ipr']



dat = [[np.trace(rj.dot(ss.ops['Y'])).real for rj in rj_list] for rj_list in sd_list]


pt.plot_spacetime_grid(dat,'ny')
plt.show()
