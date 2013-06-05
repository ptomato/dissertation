#coding: utf8

import sys
sys.path.append('..')
import numpy as N
import plot_config
import epsilons
from matplotlib import pyplot as P
from matplotlib import gridspec, patches
from diffraction import calculation_figure

# Free parameters
wl = 830e-9            # light wavelength in free space in meters
width = 26e-6          # width of view in meters
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

calc_args = {'k': kSP, 'w0': w0, 'L': L, 'res': res, 'exact': False,
    'normalize': True, 'find_zeroes': True}
axis_args = {'aspect': 'equal', 'xticks': [], 'yticks': []}
circle_args = {'facecolor': 'none', 'linestyle': 'dashed'}

ax = fig.add_subplot(gs[0], **axis_args)
p = calculation_figure(ax, 3, 50e-6, **calc_args)
# Manually put the circle in since the goddamn contour plot doesn't work
ax.add_patch(patches.Circle((0, 0), 4.0, **circle_args))
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.subfigure_label('(a)', pos='lower right')

ax = fig.add_subplot(gs[1], **axis_args)
p = calculation_figure(ax, 3.25, 50e-6, **calc_args)
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.subfigure_label('(b)', pos='lower right')

# 3.50 shows a numerical artifact that causes the vortex to split into two
# (of the same charge), for some reason - not only is this not physical, it
# didn't show up in other calculations. Using 3.51 until I can figure out what
# went wrong.
ax = fig.add_subplot(gs[2], **axis_args)
p = calculation_figure(ax, 3.51, 50e-6, **calc_args)
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.subfigure_label('(c)', pos='lower right')

ax = fig.add_subplot(gs[3], **axis_args)
p = calculation_figure(ax, 3.75, 50e-6, **calc_args)
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.subfigure_label('(d)', pos='lower right')

ax = fig.add_subplot(gs[4], **axis_args)
p = calculation_figure(ax, 4, 50e-6, **calc_args)
# Manually put the circle in since the goddamn contour plot doesn't work
ax.add_patch(patches.Circle((0, 0), 5.0, **circle_args))
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.subfigure_label('(e)', pos='lower right')

cax = fig.add_subplot(gs[5])
cb = fig.colorbar(p, cax=cax)
cb.set_label('Intensity (norm.)', labelpad=-10)
cb.set_ticks([0, 1])
cb.set_ticklabels(['0', 'max'])

fig.tight_layout()
fig.savefig('charge-evolution.pdf')

if 'batch' not in sys.argv:
    P.show()
