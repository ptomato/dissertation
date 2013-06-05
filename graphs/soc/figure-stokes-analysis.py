#coding: utf8

import sys
sys.path.append('..')
import numpy as N
from scipy import misc
import plot_config
from tango import tango
from matplotlib import pyplot as P



# fig.savefig('stokes-analysis.pdf')

if 'batch' not in sys.argv:
    P.show()
