#coding: utf8

import sys
sys.path.append('..')
import numpy as N
import plot_config
import epsilons
from matplotlib import pyplot as P
from matplotlib import gridspec
from diffraction import calculation_figure, measurement_figure

# Free parameters
wl = 830e-9            # light wavelength in free space in meters
width = 20e-6          # width of view in meters
eps2 = 1.0             # dielectric medium is air, n = 1
w0 = 2.5e-6            # width parameter of incident beam in meters
L = 50e-6              # length of slits in meters (also size of simulation)
res = 1e-7             # size of one pixel in meters

# Calculated parameters
eps1 = epsilons.epsilon_Au(wl)
k0 = 2 * N.pi / wl
kSP = k0 * N.sqrt(eps1 * eps2 / (eps1 + eps2))
lambdaSP = 2 * N.pi / kSP.real

gs = gridspec.GridSpec(2, 4, width_ratios=[1, 1, 1, 0.05])
fig1 = P.figure()
fig2 = P.figure()

axis_args = {'aspect': 'equal', 'xticks': [], 'yticks': []}

ax = fig1.add_subplot(gs[0, 0], **axis_args)
p = calculation_figure(ax, 1, 25e-6, k=kSP, w0=w0, L=L, res=res)
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.subfigure_label('(a)', pos='lower right')

ax = fig1.add_subplot(gs[0, 1], **axis_args)
reuse_plot1 = calculation_figure(ax, -1, 25e-6, k=kSP, w0=w0, L=L, res=res, normalize=True)
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.subfigure_label('(b)', pos='lower right')

ax = fig1.add_subplot(gs[0, 2], **axis_args)
p = calculation_figure(ax, -3, 25e-6, k=kSP, w0=w0, L=L, res=res)
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.subfigure_label('(c)', pos='lower right')

ax = fig1.add_subplot(gs[1, 0], **axis_args)
p = measurement_figure(ax, '../../data/20100414 l=1 measurements automated', 25)
ax.set_xlim(0, width * 1e6)
ax.set_ylim(28, 28 + width * 1e6)
ax.scale_bar(0.1, 0.05, u'10 µm', 0.5)
ax.subfigure_label('(d)', pos='lower right')

ax = fig1.add_subplot(gs[1, 1], **axis_args)
reuse_plot2 = measurement_figure(ax, '../../data/20100419 l=-1 measurements', 25)
ax.set_xlim(0, width * 1e6)
ax.set_ylim(28, 28 + width * 1e6)
ax.subfigure_label('(e)', pos='lower right')

ax = fig1.add_subplot(gs[1, 2], **axis_args)
p = measurement_figure(ax, '../../data/20100420 l=-3 measurements', 25)
ax.set_xlim(0, width * 1e6)
ax.set_ylim(31, 31 + width * 1e6)
ax.subfigure_label('(f)', pos='lower right')

cax = fig1.add_subplot(gs[:, 3])
cb = fig1.colorbar(reuse_plot1, cax=cax)
cb.set_label('Intensity (normalized)', labelpad=-10)
cb.set_ticks([0, 1])
cb.set_ticklabels(['0', 'max'])

fig1.tight_layout()
fig1.savefig('charge.pdf')

ax = fig2.add_subplot(gs[0, 0], **axis_args)
ax.add_artist(reuse_plot1)
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.subfigure_label('(a)', pos='lower right')

ax = fig2.add_subplot(gs[0, 1], **axis_args)
p = calculation_figure(ax, -1, 50e-6, k=kSP, w0=w0, L=L, res=res)
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.subfigure_label('(b)', pos='lower right')

ax = fig2.add_subplot(gs[0, 2], **axis_args)
p = calculation_figure(ax, -1, 75e-6, k=kSP, w0=w0, L=L, res=res)
ax.set_xlim(-width * 5e5, width * 5e5)
ax.set_ylim(-width * 5e5, width * 5e5)
ax.subfigure_label('(c)', pos='lower right')

ax = fig2.add_subplot(gs[1, 0], **axis_args)
ax.add_artist(reuse_plot2)
ax.set_xlim(0, width * 1e6)
ax.set_ylim(28, 28 + width * 1e6)
ax.scale_bar(0.1, 0.05, u'10 µm', 0.5)
ax.subfigure_label('(d)', pos='lower right')

ax = fig2.add_subplot(gs[1, 1], **axis_args)
p = measurement_figure(ax, '../../data/20100419 l=-1 measurements', 50)
ax.set_xlim(0, width * 1e6)
ax.set_ylim(27, 27 + width * 1e6)
ax.subfigure_label('(e)', pos='lower right')

ax = fig2.add_subplot(gs[1, 2], **axis_args)
p = measurement_figure(ax, '../../data/20100419 l=-1 measurements', 75)
ax.set_xlim(0, width * 1e6)
ax.set_ylim(27, 27 + width * 1e6)
ax.subfigure_label('(f)', pos='lower right')

cax = fig2.add_subplot(gs[:, 3])
cb = fig2.colorbar(reuse_plot1, cax=cax)
cb.set_label('Intensity (normalized)', labelpad=-10)
cb.set_ticks([0, 1])
cb.set_ticklabels(['0', 'max'])

fig2.tight_layout()
fig2.savefig('distance.pdf')

if 'batch' not in sys.argv:
    P.show()
