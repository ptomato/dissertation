#coding: utf8

import sys
sys.path.append('..')
import numpy as N
import plot_config
from tango import tango
from matplotlib import pyplot as P

# Simulation parameters (all in meters)
wavelength = 830e-9  # wavelength of light
R0 = 10e-6           # radius of slit
dR = 2e-7            # thickness of slit and groove
L = 24e-6            # side of simulation domain
res = 5e-8           # size of a pixel
n_arrows = 16        # number of arrows to draw around the circle
arrow_color = tango.skyblue1  # color of arrows

# Derived quantities
k0 = 2 * N.pi / wavelength

# Grid
dim = N.arange(-L / 2, L / 2, res)
x, y = N.meshgrid(dim, dim)
r = N.hypot(x, y)

# Calculate slit transmission
Ed = N.zeros(x.shape + (2,), dtype=complex)
Ed[..., 0] = x - y
Ed[..., 1] = x + y
Ed *= ((-x + 1j * y) / (N.sqrt(2) * r ** 2))[..., N.newaxis]
# Mask out the direct transmission everywhere except on the slit
mask = (r >= R0) & (r < R0 + dR)
Ed[..., :][~mask] = 0.0
Id = N.sum(N.abs(Ed) ** 2, axis=2)

# Pick out some coordinates for the arrows
thetas = N.linspace(0, 2 * N.pi, n_arrows, endpoint=False)
xlocs = (R0 + 0.5 * dR) * N.cos(thetas)
ylocs = (R0 + 0.5 * dR) * N.sin(thetas)
xs = N.abs(dim[:, N.newaxis] - xlocs).argmin(axis=0)
ys = N.abs(dim[:, N.newaxis] - ylocs).argmin(axis=0)

angles = N.degrees(thetas + N.pi / 4)

fig = P.figure(figsize=(plot_config.marginparwidth, plot_config.marginparwidth))
ax = fig.add_axes((0, 0, 1, 1), aspect='equal', xticks=[], yticks=[])

im = ax.imshow(Id, cmap=P.cm.gray, vmin=0, vmax=1)

# draw double-ended arrows by drawing two arrows starting at the same
# point and pointing in opposite directions
ax.quiver(xs, ys, 1, 0, angles=angles,
          width=0.012, headwidth=4, scale=10,
          color=arrow_color)
ax.quiver(xs, ys, 1, 0, angles=angles + 180.0,
          width=0.012, headwidth=4, scale=10,
          color=arrow_color)

ax.scale_bar(0.07, 0.04, u'2.4 µm', color='white')

fig.savefig('expected-near-field.pdf')

if 'batch' not in sys.argv:
    P.show()
