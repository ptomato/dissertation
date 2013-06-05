import sys
sys.path.append('..')
import numpy as N
import plot_config
from simulation import SlitSystem
from matplotlib import pyplot as P
from tango import tango

n1 = 1.00027487
n3 = 1.5102

b = N.arange(50, 830, 2) * 1e-9
calc = SlitSystem(b,
    wavelength=830e-9,
    metal_epsilon=-29.321 + 2.051j,
    metal_thickness=200e-9,
    incidence_index=n1,
    slit_index=n1,
    outcoupling_index=n3,
    collection_index=n1,
    numerical_aperture=1.0,
    angle_of_incidence=0.0,
    C1=1.0, C2=1.0)

fig = P.figure(figsize=(plot_config.textwidth, 2.75))
ax = fig.gca()

# TM transmission without surface plasmons
T_TM_no_SP = (n3 / n1) * N.abs(calc.t123_TM) ** 2
ax.plot(b * 1e9, T_TM_no_SP, color=tango.chameleon3,
    label='$T_\mathrm{TM}$ ignoring plasmons')

# Surface plasmons on the front side
SP1 = 2 * N.abs(calc.s12) ** 2
ax.plot(b * 1e9, SP1, color=tango.orange3, label='Air side plasmon loss')

# Surface plasmons on the back side
SP2 = 2 * N.abs(calc.s23) ** 2
ax.plot(b * 1e9, SP2, color=tango.plum3, label='Glass side plasmon loss')

# Total transmission
T_TM = T_TM_no_SP - SP1 - SP2
ax.plot(b * 1e9, T_TM, color=tango.scarletred3, label='Total transmission')

ax.set_xlabel('Slit width (nm)')
ax.set_ylabel('Fraction of total energy (dimensionless)')
ax.set_xlim(0, 800)
ax.legend(loc='best', prop={'size': 8})
fig.tight_layout()

fig.savefig('coupling.pdf')

if 'batch' not in sys.argv:
    P.show()
