import sys
sys.path.append('..')
import os
os.environ['TTFPATH'] = '../../fonts'
import numpy as N
from plot_config import *
import matplotlib
import matplotlib.pyplot as P
from tango import tango
from simulation import SlitSystem


def format_axes(ax, xlabel=True, ylabel=True):
    """Axis formatting common to all six plots"""
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    if xlabel:
        ax.set_xlabel('Slit width (nm)', labelpad=3)
    else:
        ax.set_xticklabels([])
    if ylabel:
        ax.set_ylabel('Normalized Stokes\nparameter (dimensionless)',
            multialignment='center',
            labelpad=0)
    else:
        ax.set_yticklabels([])
    ax.set_xticks(N.arange(0, 501, 100))
    ax.set_xticks(N.arange(50, 500, 100), minor=True)

    # Draw an extra x axis at y = 0
    ax.axhline(0, color=tango.aluminum5)

# parameters
ellipse_points_size = 8
marker_points_size = 4

# Simulation

b = N.arange(10, 830, 2) * 1e-9  # Slit width, 10-830 nm
calc = SlitSystem(b,
    wavelength=830e-9,               # Wavelength, 830 nm
    metal_epsilon=-29.321 + 2.051j,  # Relative permittivity, Au 830 nm (Palik)
    metal_thickness=200e-9,          # Film thickness, 200 nm
    incidence_index=1.00027487,
    slit_index=1.00027487,
    outcoupling_index=1.5102,
    collection_index=1.00027487,
    numerical_aperture=0.40,
    angle_of_incidence=0.0,
    C1=1.0, C2=1.0)

fig, axs = P.subplots(nrows=2, ncols=3,
    subplot_kw={
        'xlim': (0, 520),
        'ylim': (-1.05, 1.25),
    },
    subplotpars=matplotlib.figure.SubplotParams(.09, .10, .99, .94, .04, .19),
    figsize=(pagewidth, 3))

for ix, ax in enumerate(axs.flat):
    format_axes(ax, xlabel=(ix >= 3), ylabel=(ix % 3 == 0))

plots = zip(
    axs.T.flat,
    ['H', 'V', 'D', 'A', 'R', 'L'],
    [0, 1, 1, 1, 1, 1],  # E_TM
    [1, 0, 1, 1, 1, 1],  # E_TE
    [0, 0, 0, N.pi, N.pi / 2, -N.pi / 2],  # psi
)

for ax, pol, E_TM, E_TE, psi in plots:
    s1, s1err, s2, s2err, s3, s3err, width = \
        N.loadtxt('../../data/qwp/{0}-incidence.txt'.format(pol),
            skiprows=1,
            usecols=(2, 3, 4, 5, 6, 7, 9),
            unpack=True)

    # Plot data points
    ax.errorbar(width, s1, yerr=s1err,
        fmt='s',
        capsize=2,
        color=tango.scarletred3,
        markeredgecolor=tango.scarletred3)
    ax.errorbar(width, s2, yerr=s2err,
        fmt='D',
        capsize=2,
        color=tango.chameleon3,
        markeredgecolor=tango.chameleon3)
    ax.errorbar(width, s3, yerr=s3err,
        fmt='o',
        capsize=2,
        color=tango.skyblue3,
        markeredgecolor=tango.skyblue3)

    # Plot theory curve
    R = calc.T_TM / calc.T_TE
    norm = E_TE ** 2 + R * E_TM ** 2
    s1_theory = (E_TE ** 2 - R * E_TM ** 2) / norm
    s2_theory = 2 * N.sqrt(R) * E_TM * E_TE * N.cos(calc.dphase - psi) / norm
    s3_theory = -2 * N.sqrt(R) * E_TM * E_TE * N.sin(calc.dphase - psi) / norm

    ax.plot(b * 1e9, s1_theory, color=tango.scarletred3)
    ax.plot(b * 1e9, s2_theory, color=tango.chameleon3)
    ax.plot(b * 1e9, s3_theory, color=tango.skyblue3)

    poldeg = N.sqrt(s1 ** 2 + s2 ** 2 + s3 ** 2)
    linearity = N.sqrt(s1 ** 2 + s2 ** 2)
    ellipses = matplotlib.collections.EllipseCollection(
        widths=N.sqrt(0.5 * (poldeg + linearity)) * ellipse_points_size,
        heights=N.sqrt(0.5 * (poldeg - linearity)) * ellipse_points_size,
        angles=N.degrees(0.5 * N.arctan2(s2, s1)),
        facecolors='none',
        edgecolors='black',
        offsets=zip(width, N.ones_like(width) * 1.12),
        transOffset=ax.transData)
    ax.add_collection(ellipses)

axs[0, 0].set_title('(a) Incident: $s_1 = +1$')
axs[1, 0].set_title('(b) Incident: $s_1 = -1$')
axs[0, 1].set_title('(c) Incident: $s_2 = +1$')
axs[1, 1].set_title('(d) Incident: $s_2 = -1$')
axs[0, 2].set_title('(e) Incident: $s_3 = +1$')
axs[1, 2].set_title('(f) Incident: $s_3 = -1$')

# Do some legend hackery - we want the legend to display both a line and a marker
legend_lines = [
    matplotlib.lines.Line2D([], [],
        color=tango.scarletred3,
        markeredgecolor=tango.scarletred3,
        marker='s',
        linestyle='-'),
    matplotlib.lines.Line2D([], [],
        color=tango.chameleon3,
        markeredgecolor=tango.chameleon3,
        marker='D',
        linestyle='-'),
    matplotlib.lines.Line2D([], [],
        color=tango.skyblue3,
        markeredgecolor=tango.skyblue3,
        marker='o',
        linestyle='-')
]
axs[0, 0].legend(legend_lines, ['$s_1$', '$s_2$', '$s_3$'],
    loc='best',
    numpoints=1,
    labelspacing=0,
    borderaxespad=0.1,
    frameon=False)

fig.savefig('stokes-parameters.pdf')

if 'batch' not in sys.argv:
    P.show()
