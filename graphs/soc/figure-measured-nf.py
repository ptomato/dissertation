#coding: utf8

import sys
sys.path.append('..')
import numpy as N
from scipy import misc, ndimage
import plot_config
from tango import tango
from matplotlib import pyplot as P
from matplotlib import collections


def polarcoords(outcoords, centercoords, ntheta, nr, rmax):
    """
    Coordinate transform for converting a Cartesian image to polar coordinates.
    Theta goes from 0 to 2 pi in ntheta steps, R goes from 0 to rmax in nr steps.
    centercoords is a tuple containing the position of the origin in the XY array.
    """
    # Calculate the mathematical R and Theta from the image coordinates by scaling
    outr, outtheta = outcoords
    R = rmax * (outr / float(nr))
    Theta = 2 * N.pi * (outtheta / float(ntheta))

    X0, Y0 = centercoords

    X = R * N.cos(Theta - N.pi / 2) + X0
    Y = R * N.sin(Theta - N.pi / 2) + Y0

    return (X, Y)

datapath = '../../data/20120210 Stokes analysis SOC/'

# Load near-field image
nf_data = misc.imread(datapath + 'image of ring.png', flatten=True)[195:275, 430:350:-1]

# Load Stokes parameters
St = [N.loadtxt(datapath + 'A1_slit_S{}.txt'.format(count))[7:, 1:-3][:, ::-1]
      for count in range(4)]
St[2] *= -1  # crap, correct for different definition of handedness

xlen, ylen = St[0].shape
rin, rout = 24, 34
polarshape = (rout, 90)
averages = []
for image in St:
    extra_keywords = {'centercoords': (xlen / 2, ylen / 2),
                      'ntheta': polarshape[1],
                      'nr': polarshape[0],
                      'rmax': rout}
    transformed = ndimage.geometric_transform(image, polarcoords,
        output_shape=polarshape, order=1, extra_keywords=extra_keywords)
    averages += [transformed[rin:rout, :].mean(0)]

theta = N.linspace(0, 360, num=polarshape[1], endpoint=True)
Ip = N.sqrt((averages[1] ** 2.0 + averages[2] ** 2.0 + averages[3] ** 2.0) / averages[0] ** 2.0)
modL = N.sqrt((averages[1] ** 2.0 + averages[2] ** 2.0) / averages[0] ** 2.0)
widths = N.sqrt(0.5 * (Ip + modL))
heights = N.sqrt(0.5 * (Ip - modL))
angles = 0.5 * N.arctan2(averages[2], averages[1]) * 180.0 / N.pi
lhcp_mask = ((averages[3] / averages[0]) < -0.1)
rhcp_mask = ((averages[3] / averages[0]) > 0.1)
lin_mask = ~(lhcp_mask | rhcp_mask)
offsets = N.hstack(((theta[:, N.newaxis]) * N.pi / 180.0,
    N.ones_like(theta[:, N.newaxis]) * 7.0))


# plot it
fig = P.figure(figsize=(plot_config.textwidth, 2.0))
ax = fig.add_subplot(1, 2, 1, aspect='equal', xticks=[], yticks=[])
im = ax.imshow(nf_data)
ax.subfigure_label('(a)')
fig.tight_layout()
fig.nice_colorbar(im, ticks=[])

ax = fig.add_subplot(1, 2, 2, polar=True, frame_on=False)
ellipse_args = {
    'units': 'xy',
    'facecolors': 'none',
    'linewidth': 0.5,
    'transOffset': ax.transData
}
ec_RHCP = collections.EllipseCollection(
    widths=widths[rhcp_mask],
    heights=heights[rhcp_mask],
    angles=angles[rhcp_mask],
    edgecolors=tango.skyblue3,
    offsets=offsets[rhcp_mask],
    **ellipse_args)
ec_LHCP = collections.EllipseCollection(
    widths=widths[lhcp_mask],
    heights=heights[lhcp_mask],
    angles=angles[lhcp_mask],
    edgecolors=tango.scarletred3,
    offsets=offsets[lhcp_mask],
    **ellipse_args)
ec_lin = collections.EllipseCollection(
    widths=widths[lin_mask],
    heights=heights[lin_mask],
    angles=angles[lin_mask],
    edgecolors='black',
    offsets=offsets[lin_mask],
    **ellipse_args)
ax.add_collection(ec_LHCP)
ax.add_collection(ec_RHCP)
ax.add_collection(ec_lin)

ax.set_ylim(0, 8)
ax.set_xticks([])  # doesn't work from add_subplot() call?!
ax.set_yticks([])
ax.subfigure_label('(b)')

# Create proxy artists for the ellipse collections, which aren't supported
# by legend()
proxy_r = P.Line2D([0], [0], color=tango.skyblue3)
proxy_l = P.Line2D([0], [0], color=tango.scarletred3)
proxy_lin = P.Line2D([0], [0], color='black')
ax.legend((proxy_r, proxy_l, proxy_lin),
    ('Right-handed', 'Left-handed', 'Approx. linear'),
    loc='center',
    frameon=False)

fig.savefig('measured-near-field.pdf')

# plot unrolled figure

fig = P.figure()
ax = fig.gca()

# Calculated
angles = N.linspace(0, 2 * N.pi, 200)
ax.plot(angles, -N.sin(2 * angles), color=tango.skyblue3, label='')
ax.plot(angles, N.cos(2 * angles), color=tango.scarletred3, label='')
ax.plot(angles, N.zeros_like(angles), color=tango.chameleon3, label='')

# Measured
m_angles = N.radians(N.arange(0, 360, 8))
plot_args = {'linestyle': 'none', 'markeredgewidth': 0}
ax.plot(m_angles, (averages[1] / averages[0])[::2],
        color=tango.skyblue3, markeredgecolor=tango.skyblue3,
        marker='s', label='$s_1$', **plot_args)
ax.plot(m_angles, (averages[2] / averages[0])[::2],
        color=tango.scarletred3, markeredgecolor=tango.scarletred3,
        marker='D', label='$s_2$', **plot_args)
ax.plot(m_angles, (averages[3] / averages[0])[::2],
        color=tango.chameleon3, markeredgecolor=tango.chameleon3,
        marker='o', label='$s_3$', **plot_args)
ax.set_xlim(0, 2 * N.pi)
ax.set_xticks(N.arange(0, 2.1, 0.5) * N.pi)
ax.set_xticks(N.arange(0, 2.1, 0.25) * N.pi, minor=True)
ax.set_xticklabels(['0', r'$\pi/2$', r'$\pi$', r'$3\pi/2$', r'$2\pi$'])
# ax.tick_params(axis='both', direction='out',
#                length=2, width=0.5, top='off', right='off')
# ax.tick_params(axis='y', pad=0)
# ax.tick_params(axis='x', pad=5)
ax.set_xlabel('Azimuthal angle (rad)')
ax.set_ylabel('Normalized Stokes\nparameter (dimensionless)',
              horizontalalignment='center')
ax.set_ylim(-1.1, 1.1)
ax.legend(numpoints=1, loc='best')

fig.tight_layout()
fig.savefig('stokes-analysis.pdf')

if 'batch' not in sys.argv:
    P.show()
