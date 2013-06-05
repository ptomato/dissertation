#coding: utf8

import sys
sys.path.append('..')
import numpy as N
import plot_config
import epsilons
from tango import tango
from matplotlib import pyplot as P
from matplotlib import gridspec
from diffraction import calculation_figure, grid, vortex_beam

# Free parameters
wl = 830e-9            # light wavelength in free space in meters
width = 14e-6          # width of view in meters
eps2 = 1.0             # dielectric medium is air, n = 1
w0 = 2.5e-6            # width parameter of incident beam in meters
L = 50e-6              # length of slits in meters (also size of simulation)
res = 1e-7             # size of one pixel in meters

# Calculated parameters
eps1 = epsilons.epsilon_Au(wl)
k0 = 2 * N.pi / wl
kSP = k0 * N.sqrt(eps1 * eps2 / (eps1 + eps2))

linecolor = tango.scarletred1

gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 0.05])
fig = P.figure(figsize=(plot_config.textwidth, 1.9))

axis_args = {'aspect': 'equal', 'xticks': [], 'yticks': []}
vline_args = {'color': linecolor}
annotation_args = {
    'xytext': (-1, -5),
    'textcoords': 'offset points',
    'color': linecolor,
    'horizontalalignment': 'right',
    'verticalalignment': 'top'}
xmarker_args = {
    'color': linecolor,
    'marker': 'x'}
omarker_args = {
    'color': linecolor,
    'marker': 'o',
    'markeredgecolor': linecolor,
    'markerfacecolor': 'none'}

half = 250
side = 236
ring = 218  # maximum of the original ring; max of tomogram is 228
data_transform = lambda x: (x - half) * res * 1e6

ax1 = fig.add_subplot(gs[0], **axis_args)
_, _, r, theta = grid(L, res)
vortex = N.abs(vortex_beam(r, theta, -3, w0)) ** 2
hw = L * 5e5  # halfwidth of view
p = ax1.imshow(vortex, extent=(-hw, hw, -hw, hw))
ax1.set_xlim(-width * 5e5, width * 5e5)
ax1.set_ylim(-width * 5e5, width * 5e5)
ax1.subfigure_label('(a)', pos='lower right')

ax1.axvline(x=data_transform(half), **vline_args)
ax1.axvline(x=data_transform(side), **vline_args)
ax1.axvline(x=data_transform(ring), **vline_args)

ax2 = fig.add_subplot(gs[1], **axis_args)
field, p = calculation_figure(ax2, -3, 25e-6,
    k=kSP, w0=w0, L=L, res=res, normalize=True, return_field=True)
ax2.set_xlim(-width * 5e5, width * 5e5)
ax2.set_ylim(-width * 5e5, width * 5e5)
ax2.subfigure_label('(b)', pos='lower right')
ax2.axvline(x=data_transform(half), **vline_args)
ax2.plot([data_transform(half)], [data_transform(field[:, half].argmin())],
    **xmarker_args)
ax2.plot([data_transform(half)],
    [data_transform(field[half:, half].argmax() + half)],
    **omarker_args)
ax2.plot([data_transform(half)], [data_transform(field[:half, half].argmax())],
    **omarker_args)

ax2.axvline(x=data_transform(side), **vline_args)
max1 = field[:half, side].argmax()
max2 = field[half:, side].argmax() + half
ax2.plot([data_transform(side)], [data_transform(field[max1:max2, side].argmin() + max1)],
    **xmarker_args)
ax2.plot([data_transform(side)], [data_transform(max1)], **omarker_args)
ax2.plot([data_transform(side)], [data_transform(max2)], **omarker_args)

ax2.axvline(x=data_transform(ring), **vline_args)
ax2.plot([data_transform(ring)], [data_transform(field[:, ring].argmax())],
    **omarker_args)

ax1.annotate('(1)', (data_transform(ring), width * 5e5), **annotation_args)
ax2.annotate('(1)', (data_transform(ring), width * 5e5), **annotation_args)
ax1.annotate('(2)', (data_transform(side), width * 5e5), **annotation_args)
ax2.annotate('(2)', (data_transform(side), width * 5e5), **annotation_args)
ax1.annotate('(3)', (data_transform(half), width * 5e5), **annotation_args)
ax2.annotate('(3)', (data_transform(half), width * 5e5), **annotation_args)

cax = fig.add_subplot(gs[2])
cb = fig.colorbar(p, cax=cax)
cb.set_label('Intensity (normalized)', labelpad=-10)
cb.set_ticks([0, 1])
cb.set_ticklabels(['0', 'max'])

fig.tight_layout()
fig.savefig('diffraction.pdf')

if 'batch' not in sys.argv:
    P.show()
