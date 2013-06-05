#coding: utf8

import sys
sys.path.append('..')
import numpy as N
from numpy import ma
from scipy import misc
from scipy.special import j0, jn
from scipy.ndimage.interpolation import affine_transform
from scipy.ndimage.filters import gaussian_filter
from matplotlib.colors import ListedColormap
from matplotlib import pyplot as P
import matplotlib
from mpl_toolkits.axes_grid1 import ImageGrid
import plot_config
from tango import tango


def slice2d(center, width):
    return (slice(int(center[0] - width / 2), int(center[0] + width / 2)),
            slice(int(center[1] - width / 2), int(center[1] + width / 2)))


def rolling_window(a, window_shape):
    """Generalization of
    http://www.rigtorp.se/2011/01/01/rolling-statistics-numpy.html"""
    window_dim = len(window_shape)
    shape = (a.shape[:-window_dim]
             + tuple([a.shape[-1 - n] - window_shape[n] + 1
                for n in xrange(window_dim)])
             + window_shape)
    strides = a.strides + a.strides[-window_dim:]
    return N.lib.stride_tricks.as_strided(a,
        shape=shape, strides=strides)

datapath = '../../data/20120210 Stokes analysis SOC/'

# Simulation parameters
wavelength = 800e-9
R0 = 10e-6          # radius of slit

# These measurements are in the spatial frequency domain
max_angle = 0.25  # max angle in either direction in radians
num_pixels = 500
L = N.sin(max_angle) / wavelength  # size of simulation domain
res = L / num_pixels  # pixel size

# Extents in angular space
mx = max_angle / N.pi
size = (-mx, mx, -mx, mx)

# Grid
side = N.arange(-L / 2, L / 2, res)
x, y = N.meshgrid(side, side)
r, theta = N.hypot(x, y), N.arctan2(y, x)

# Calculate far field
pi2r = 2 * N.pi * r
EFF0 = N.ones(x.shape + (2,), dtype=complex)
EFF0[..., 0] = 1.0j
EFF0 *= j0(pi2r * R0)[..., N.newaxis]

EFF1 = N.ones_like(EFF0)
EFF1[..., 1] = 1.0j
EFF1 *= (N.exp(2j * theta) * jn(2, pi2r * R0))[..., N.newaxis]

data_b = misc.imread(datapath + 'intensity Q0.png', flatten=True)
data_c = misc.imread(datapath + 'phase Q0.png', flatten=True)
data_e = misc.imread(datapath + 'intensity Q2.png', flatten=True)
data_f = misc.imread(datapath + 'phase Q2.png', flatten=True)

center_b = N.unravel_index(N.argmax(data_b), data_b.shape)
width_b = 180
slice_b = slice2d(center_b, width_b)

#from scipy.ndimage.measurements import center_of_mass
#center_c = center_of_mass(data_c)
#width_c = 170
#slice_c = slice2d(center_c, width_c)
slice_c = slice_b

# Crop data
data_b = data_b[slice_b]
data_c = data_c[slice_c]
data_e = data_e[slice_b]
data_f = data_f[slice_c]

# Draw figure
fig = P.figure(figsize=(plot_config.textwidth, 2.5))
grid = ImageGrid(fig, [0, 0, 1, 1], (2, 3),
    cbar_mode='each',
    axes_pad=0.075,
    cbar_pad=0)

colorbar_args = {
    'ticks': [],
    'format': matplotlib.ticker.NullFormatter()
}

ax = grid[0]
im = ax.field_plot((1 - 1j) * EFF0[..., 1], extent=size)
ax.set_xticks([])
ax.set_yticks([])
ax.cax.colorbar(im, ticks=N.arange(0, 1, 0.25),
                format=matplotlib.ticker.NullFormatter())
ax.subfigure_label('(a)', color='white')
ax.scale_bar(0.8, 0.1, '50 mrad', color='white', fontdict={'size': 6})

ax = grid[1]
im = ax.imshow(data_b, extent=size)
ax.set_xticks([])
ax.set_yticks([])
ax.cax.colorbar(im, **colorbar_args)
ax.subfigure_label('(b)')

ax = grid[2]
im = ax.imshow(data_c, extent=size)
ax.set_xticks([])
ax.set_yticks([])
ax.cax.colorbar(im, **colorbar_args)
ax.subfigure_label('(c)')

ax = grid[3]
im = ax.field_plot(-(1 + 1j) * EFF1[..., 0], extent=size)
ax.set_xticks([])
ax.set_yticks([])
ax.cax.colorbar(im, ticks=N.arange(0, 1, 0.25),
                format=matplotlib.ticker.NullFormatter())
ax.subfigure_label('(d)', color='white')
ax.scale_bar(0.8, 0.1, '50 mrad', color='white', fontdict={'size': 6})

ax = grid[4]
im = ax.imshow(data_e, extent=size)
ax.set_xticks([])
ax.set_yticks([])
ax.cax.colorbar(im, **colorbar_args)
ax.subfigure_label('(e)')

ax = grid[5]
im = ax.imshow(data_f, extent=size)
ax.set_xticks([])
ax.set_yticks([])
ax.cax.colorbar(im, **colorbar_args)
ax.subfigure_label('(f)')

# Find the fringes!
scaling = 4
zoomed_data = affine_transform(data_f,
    N.array((1.0 / scaling, 1.0 / scaling)),
    output_shape=(width_b * scaling, width_b * scaling))
zoomed_data = gaussian_filter(zoomed_data, 2)

# L.Z. Cai, Q. Liu, X.L. Yang (2003). A simple method of contrast
# enhancement and extremum extraction for interference fringes. Optics &
# Laser Technology 35 (4), 295–302
# http://www.sciencedirect.com/science/article/pii/S0030399203000227
n = 2  # empirically determined
window = rolling_window(zoomed_data, (2 * n + 1, 2 * n + 1))
enhanced_image = (0.5
    + (window[..., n, n] - window.mean(-1).mean(-1))
    / (window.max(-1).max(-1) - window.min(-1).min(-1)))
# Pad the enhanced image to recover the lost pixels on the edges
zero = N.zeros_like(zoomed_data)
zero[n:-n, n:-n] = enhanced_image
# in numpy 1.7: enhanced_image = N.pad(enhanced_image, n,
# mode='constant', constant_values=1)
enhanced_image = zero

# threshold the enhanced image
enhanced_image = ma.masked_greater(enhanced_image, 0.42, copy=False)
# porthole the enhanced image
x, y = N.meshgrid(
    N.arange(enhanced_image.shape[0]),
    N.arange(enhanced_image.shape[1]))
x -= x.shape[0] / 2
y -= y.shape[1] / 2
enhanced_image = ma.masked_where(N.hypot(x, y) > 150, enhanced_image,
    copy=False)

# Forces some recalculation?! otherwise ax.get_position() doesn't work
ax.get_tightbbox(True)

newax = fig.add_axes(ax.get_position(),
    frameon=False, xticks=[], yticks=[])
newax.imshow(enhanced_image, cmap=ListedColormap([tango.scarletred1]),
    extent=size)

fig.savefig('far-field-measurements.pdf')

if 'batch' not in sys.argv:
    P.show()
