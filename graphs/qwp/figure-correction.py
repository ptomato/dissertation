import sys
sys.path.append('..')
import numpy as N
import plot_config
import matplotlib.pyplot as P
from simulation import SlitSystem
from tango import tango
from epsilons import epsilon_Au

wl = 800e-9
n_air = 1.0
n_glass = 1.5
high_na = 0.8
low_na = 0.2
widths = N.arange(100, 501, 10) * 1e-9
k0 = 2 * N.pi / wl

fig1 = P.figure(figsize=(plot_config.pagewidth, 2.5))
# fig2 = P.figure(figsize=(plot_config.pagewidth, 2.5))

calc = SlitSystem(
    slit_widths=widths,
    wavelength=wl,
    metal_epsilon=epsilon_Au(wl),
    metal_thickness=200e-9,
    incidence_index=n_glass,
    slit_index=n_air,
    outcoupling_index=n_air,
    collection_index=n_air,
    numerical_aperture=low_na,
    angle_of_incidence=0.0,
    caching=False)

ratio1 = calc.collection_eff_TM / calc.collection_eff_TE
# absolute1 = calc.collection_eff_TE

calc = SlitSystem(
    slit_widths=widths,
    wavelength=wl,
    metal_epsilon=epsilon_Au(wl),
    metal_thickness=200e-9,
    incidence_index=n_glass,
    slit_index=n_air,
    outcoupling_index=n_air,
    collection_index=n_air,
    numerical_aperture=high_na,
    angle_of_incidence=0.0,
    caching=False)

ratio2 = calc.collection_eff_TM / calc.collection_eff_TE
# absolute2 = calc.collection_eff_TE

ax = fig1.add_subplot(1, 2, 1)
ax.axhline(1.0, color=tango.aluminum3, linestyle='--')
ax.plot(widths * 1e9, ratio1, color=tango.plum3, label='Low NA')
ax.plot(widths * 1e9, ratio2, color=tango.chameleon3, label='High NA')
ax.legend(loc='best')
ax.set_xlabel('Slit width (nm)')
ax.set_ylabel('$C_{TM}/C_{TE}$ (dimensionless)')
ax.set_xlim(100, 500)
ax.set_ylim(0.94, 1.08)
ax.set_title('(a) Reverse illumination')
# ax.subfigure_label('(a)', pos='lower right')

# ax = fig2.add_subplot(1, 2, 1)
# ax.plot(widths * 1e9, absolute1, color=tango.plum3, label='Low NA')
# ax.plot(widths * 1e9, absolute2, color=tango.chameleon3, label='High NA')
# ax.legend(loc='best')
# ax.set_xlabel('Slit width (nm)')
# ax.set_ylabel('Fraction of collected energy (dimensionless)')
# ax.set_xlim(100, 500)
# ax.set_ylim(0, 1)
# ax.subfigure_label('(a)')

calc = SlitSystem(
    slit_widths=widths,
    wavelength=wl,
    metal_epsilon=epsilon_Au(wl),
    metal_thickness=200e-9,
    incidence_index=n_air,
    slit_index=n_air,
    outcoupling_index=n_glass,
    collection_index=n_air,
    numerical_aperture=low_na,
    angle_of_incidence=0.0,
    caching=False)

ratio1 = calc.collection_eff_TM / calc.collection_eff_TE
# absolute1 = calc.collection_eff_TE

calc = SlitSystem(
    slit_widths=widths,
    wavelength=wl,
    metal_epsilon=epsilon_Au(wl),
    metal_thickness=200e-9,
    incidence_index=n_air,
    slit_index=n_air,
    outcoupling_index=n_glass,
    collection_index=n_air,
    numerical_aperture=high_na,
    angle_of_incidence=0.0,
    caching=False)

ratio2 = calc.collection_eff_TM / calc.collection_eff_TE
# absolute2 = calc.collection_eff_TE

ax = fig1.add_subplot(1, 2, 2)
ax.axhline(1.0, color=tango.aluminum3, linestyle='--')
ax.plot(widths * 1e9, ratio1, color=tango.plum3, label='Low NA')
ax.plot(widths * 1e9, ratio2, color=tango.chameleon3, label='High NA')
ax.legend(loc='best')
ax.set_xlabel('Slit width (nm)')
ax.set_xlim(100, 500)
ax.set_title('(b) Forward illumination')
# ax.subfigure_label('(b)', pos='lower right')

# ax = fig2.add_subplot(1, 2, 2)
# ax.plot(widths * 1e9, absolute1, color=tango.plum3, label='Low NA')
# ax.plot(widths * 1e9, absolute2, color=tango.chameleon3, label='High NA')
# ax.legend(loc='best')
# ax.set_xlabel('Slit width (nm)')
# ax.set_xlim(100, 500)
# ax.set_ylim(0, 1)
# ax.subfigure_label('(b)')

fig1.tight_layout()
fig1.savefig('correction-factors.pdf')

# fig2.tight_layout()
# fig2.savefig('correction-fractions.pdf')

if 'batch' not in sys.argv:
    P.show()
