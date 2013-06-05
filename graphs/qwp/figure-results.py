import sys
sys.path.append('..')
import numpy as N
import plot_config
import matplotlib
import matplotlib.pyplot as P
from simulation import SlitSystem
from tango import tango

# Experimental data
data_width, tm, tm_err = N.loadtxt('../../data/qwp/Johan-TM.txt',
    usecols=(4, 5, 6),
    skiprows=1,
    unpack=True)
te, te_err = N.loadtxt('../../data/qwp/Johan-TE.txt',
    usecols=(5, 6),
    skiprows=1,
    unpack=True)


def load_dphase(character, psi, order):
    s1, s1err, s2, s2err, s3, s3err = N.loadtxt(
        '../../data/qwp/{0}-incidence.txt'.format(character),
        skiprows=1,
        usecols=(2, 3, 4, 5, 6, 7),
        unpack=True)

    # The error cannot be so large that it makes the absolute value of the
    # Stokes parameter larger than 1
    # This should be done with asymmetrical error propagation, but it affects
    # so few values, it's not worth bothering with.
    s1err[-(N.abs(s1) - 1) < s1err] = -(N.abs(s1) - 1)[-(N.abs(s1) - 1) < s1err]
    s2err[-(N.abs(s2) - 1) < s2err] = -(N.abs(s2) - 1)[-(N.abs(s2) - 1) < s2err]
    s3err[-(N.abs(s3) - 1) < s3err] = -(N.abs(s3) - 1)[-(N.abs(s3) - 1) < s3err]

    R = -(s1 - 1) / (s1 + 1)
    R_err = 2 * s1err / (s1 + 1) ** 2

    acs = N.arccos((s2 * (R + 1) / (2 * N.sqrt(R))).clip(-1, 1))
    asn = N.arcsin((s3 * (R + 1) / (2 * N.sqrt(R))).clip(-1, 1))
    dphase = [
        (psi + acs) % (2 * N.pi),
        (psi - asn) % (2 * N.pi),
        (psi - acs) % (2 * N.pi),  # Other solution of arccos
        (psi + asn + N.pi) % (2 * N.pi)  # Other solution of arcsin
    ]

    acs_err = N.sqrt((2 * s2err * R * (R + 1)) ** 2 + (R_err * s2 * (R - 1)) ** 2) \
        / (2 * R * N.sqrt(N.abs(((R + 1) * s2) ** 2 - 4 * R)))
    asn_err = N.sqrt((2 * s3err * R * (R + 1)) ** 2 + (R_err * s3 * (R - 1)) ** 2) \
        / (2 * R * N.sqrt(N.abs(((R + 1) * s3) ** 2 - 4 * R)))

    dphase_err = [
        acs_err,
        asn_err,
        acs_err,
        asn_err
    ]

    # Two solutions
    return (N.column_stack([
            dphase[order[0]],
            N.append(dphase[order[1]][:7], dphase[order[2]][7:])
        ]), N.column_stack([
            dphase_err[order[0]],
            N.append(dphase_err[order[1]][:7], dphase_err[order[2]][7:])
        ]))

data_dphase_val_and_err = [
    load_dphase('D', 0, (0, 1, 3)),
    load_dphase('A', N.pi, (2, 3, 1)),
    load_dphase('R', N.pi / 2, (1, 2, 0)),
    load_dphase('L', -N.pi / 2, (3, 0, 2))
]
# Take the average of all the solutions and the average of all the errors
data_dphase = N.mean(
    N.column_stack([val[0] for val in data_dphase_val_and_err]),
    axis=1)
data_dphase_err = N.mean(
    N.column_stack([val[1] for val in data_dphase_val_and_err]),
    axis=1)

# Simulation

b = N.arange(15, 830, 2) * 1e-9  # Slit width, 15-830 nm
calc = SlitSystem(b,
    wavelength=830e-9,               # Wavelength, 830 nm
    metal_epsilon=-29.321 + 2.051j,  # Relative permittivity, Au 830 nm (Palik)
    metal_thickness=210e-9,          # Film thickness, 210 nm
    incidence_index=1.00027487,
    slit_index=1.00027487,
    outcoupling_index=1.5102,
    collection_index=1.00027487,
    numerical_aperture=0.40,
    angle_of_incidence=0.0,
    C1=1.0, C2=1.0)

# Normalize to transmission at w=500 nm
T_TM = calc.T_TM / calc.T_TE[N.abs(b - 5e-7) < 1e-9]
T_TE = calc.T_TE / calc.T_TE[N.abs(b - 5e-7) < 1e-9]

fig1 = P.figure()
ax = fig1.gca()

ax.errorbar(data_width, tm, yerr=tm_err,
    fmt='s',
    color=tango.scarletred3,
    markeredgecolor=tango.scarletred3)
ax.errorbar(data_width, te, yerr=te_err,
    fmt='o',
    color=tango.skyblue3,
    markeredgecolor=tango.skyblue3)
ax.plot(b * 1e9, T_TM, tango.scarletred3)
ax.plot(b * 1e9, T_TE, tango.skyblue3)

ax.set_xlabel('Slit width (nm)')
ax.set_ylabel('Transmission (dimensionless)')
ax.set_xlim(0, 500)
ax.set_ylim(0, 1)

# Do some legend hackery -
# we want the legend to display both a line and a marker
legend_lines = [
    matplotlib.lines.Line2D([], [],
        color=tango.scarletred3,
        markeredgecolor=tango.scarletred3,
        marker='s',
        linestyle='-'),
    matplotlib.lines.Line2D([], [],
        color=tango.skyblue3,
        markeredgecolor=tango.skyblue3,
        marker='o',
        linestyle='-')
]
ax.legend(legend_lines, ['TM', 'TE'], loc='best', numpoints=1)
fig1.tight_layout()

fig2 = P.figure()
ax = fig2.gca()
ax.plot(b * 1e9, calc.dphase / N.pi, 'black')
ax.errorbar(data_width, data_dphase / N.pi % 2,
    yerr=data_dphase_err / N.pi,
    fmt='ks')
ax.annotate(r'$\pi/2$', (230, 0.55),
    xytext=(20, 20),
    textcoords='offset points',
    va='center',
    ha='center',
    size='large',
    bbox={
        'boxstyle': 'round',
        'facecolor': tango.aluminum2,
        'edgecolor': 'none'
    },
    arrowprops={
        'facecolor': tango.aluminum2,
        'edgecolor': 'none',
        'arrowstyle': 'wedge,tail_width=0.5',
        'connectionstyle': 'arc3',
        'patchA': None
    })
ax.axhline(y=0.5, xmin=0, xmax=0.47,
    color=tango.aluminum3,
    linestyle='--', zorder=0)
ax.axvline(x=235, ymin=0, ymax=0.4,
    color=tango.aluminum3,
    linestyle='--')
ax.set_xlim(0, 500)
ax.set_xlabel('Slit width (nm)')
ax.set_ylabel('Phase difference TM-TE (rad)')
ax.set_ylim(0, 1.25)
ax.set_yticks(N.linspace(0, 1.25, 11), minor=True)
ax.set_yticks(N.linspace(0, 1.25, 6))
ax.set_yticklabels(['0', r'$\pi/4$', r'$\pi/2$', r'$3\pi/4$', r'$\pi$', r'$5\pi/4$'])
fig2.tight_layout()

fig1.savefig('dichroism.pdf')
fig2.savefig('birefringence.pdf')

if 'batch' not in sys.argv:
    P.show()
