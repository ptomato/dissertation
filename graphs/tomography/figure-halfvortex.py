#coding: utf8

import sys
sys.path.append('..')
import numpy as N
from scipy import misc
import plot_config
import epsilons
from matplotlib import pyplot as P
from matplotlib import gridspec
from diffraction import calculation_figure, measurement_figure

# Free parameters
wl = 830e-9            # light wavelength in free space in meters
width = 20e-6          # width of view in meters
eps2 = 1.0             # dielectric medium is air, n = 1
w0 = 2.2e-6            # width parameter of incident beam in meters
L = 50e-6              # length of slits in meters (also size of simulation)
res = 1e-7             # size of one pixel in meters

# Calculated parameters
eps1 = epsilons.epsilon_Au(wl)
k0 = 2 * N.pi / wl
kSP = k0 * N.sqrt(eps1 * eps2 / (eps1 + eps2))

gs = gridspec.GridSpec(1, 6, width_ratios=[1, 1, 1, 1, 1, 0.05])
fig = P.figure(figsize=(plot_config.pagewidth, 1.21))

axis_args = {'aspect': 'equal', 'xticks': [], 'yticks': []}

ax = fig.add_subplot(gs[0], **axis_args)
reflection = misc.imread('../../data/20100429 l=3.5 plate/far field.png')[150:350, 115:315]
ax.imshow(reflection, origin='upper')
ax.subfigure_label('(a)', pos='lower_right')

ax = fig.add_subplot(gs[1], **axis_args)
p = measurement_figure(ax, '../../data/20100429 l=3.5 plate', 25)
ax.set_xlim(0, width * 1e6)
ax.set_ylim(33, 33 + width * 1e6)
ax.scale_bar(0.1, 0.05, u'10 µm', 0.5)
ax.subfigure_label('(b)', pos='lower right')

ax = fig.add_subplot(gs[2], **axis_args)
p = measurement_figure(ax, '../../data/20100429 l=3.5 plate', 75)
ax.set_xlim(0, width * 1e6)
ax.set_ylim(33, 33 + width * 1e6)
ax.scale_bar(0.1, 0.05, u'10 µm', 0.5)
ax.subfigure_label('(c)', pos='lower right')

width = 26e-6

ax = fig.add_subplot(gs[3], **axis_args)
p = calculation_figure(ax, 3.5, 25e-6, k=kSP, w0=w0, L=L, res=res, exact=False, normalize=True)
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.scale_bar(0.1, 0.05, u'10 µm', 10.0 / 26.0)
ax.subfigure_label('(d)', pos='lower right')

ax = fig.add_subplot(gs[4], **axis_args)
p = calculation_figure(ax, 3.5, 75e-6, k=kSP, w0=w0, L=L, res=res, exact=False, normalize=True)
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.scale_bar(0.1, 0.05, u'10 µm', 10.0 / 26.0)
ax.subfigure_label('(e)', pos='lower right')

cax = fig.add_subplot(gs[5])
cb = fig.colorbar(p, cax=cax)
cb.set_label('Intensity (norm.)', labelpad=-10)
cb.set_ticks([0, 1])
cb.set_ticklabels(['0', 'max'])

fig.tight_layout()
fig.savefig('halfvortex.pdf')

if 'batch' not in sys.argv:
    P.show()
