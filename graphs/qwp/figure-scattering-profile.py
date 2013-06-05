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
k0 = 2 * N.pi / wl
w = 250e-9

calc = SlitSystem(
    slit_widths=N.array([w]),
    wavelength=wl,
    metal_epsilon=epsilon_Au(wl),
    metal_thickness=200e-9,
    incidence_index=n_air,
    slit_index=n_air,
    outcoupling_index=n_glass,
    collection_index=n_air,
    numerical_aperture=0.8,
    angle_of_incidence=0.0,
    caching=False)

freqs = N.r_[-calc.spatial_frequencies[::-1], calc.spatial_frequencies] / 1e6

fig = P.figure(figsize=(plot_config.pagewidth, 2.5))
# ax = fig1.add_subplot(1, 2, 1)
# ax.plot(freqs, N.abs(N.r_[calc.Fy_TE[::-1], calc.Fy_TE]) ** 2,
#     tango.skyblue3,
#     label='$|F_y^{TE}(f_X)|^2$')
# ax.plot(freqs, N.abs(N.r_[calc.Fx_TM[::-1], calc.Fx_TM]) ** 2,
#     tango.scarletred3,
#     label='$|F_x^{TM}(f_X)|^2$')
# ax.set_xlim(-30, 30)
# ax.set_xlabel(u'Transverse spatial frequency (µm$^{-1}$)')
# ax.set_ylabel('Intensity (arb. units)')
# ax.legend(loc='best')

angles = N.r_[-calc.angles[::-1], calc.angles]
Fy_TE2 = N.r_[calc.Fy_TE2[::-1], calc.Fy_TE2]
Fx_TM2 = N.r_[calc.Fx_TM2[::-1], calc.Fx_TM2]

ax = fig.add_subplot(1, 2, 1)
ax.plot(angles / N.pi, Fy_TE2,
    tango.skyblue3,
    label=r'$|F_y^{TE}(\theta)|^2$')
ax.plot(angles / N.pi, Fx_TM2,
    tango.scarletred3,
    label=r'$|F_x^{TM}(\theta)|^2$')
ax.legend(loc='best')
ax.set_xlim(-0.5, 0.5)
ax.set_ylim(0, 0.014)
ax.set_xlabel('Scattering angle (rad)')
ax.set_ylabel('Fourier component (arb. units)')
ax.set_xticks([-0.5, -0.25, 0, 0.25, 0.5])
ax.set_xticklabels([r'$-\pi/2$', r'$-\pi/4$', '0', r'$\pi/4$', r'$\pi/2$'])

ax = fig.add_subplot(1, 2, 2)
ax.plot(angles / N.pi, 1 - N.r_[calc.R_TE[::-1], calc.R_TE],
    tango.skyblue3,
    label=r'$T_{TE}(\theta)$')
ax.plot(angles / N.pi, 1 - N.r_[calc.R_TM[::-1], calc.R_TM],
    tango.scarletred3,
    label=r'$T_{TM}(\theta)$')
ax.legend(loc='best')
ax.set_xlim(-0.5, 0.5)
ax.set_xlabel('Scattering angle (rad)')
ax.set_ylabel('Transmission at interface (dimensionless)')
ax.set_xticks([-0.5, -0.25, 0, 0.25, 0.5])
ax.set_xticklabels([r'$-\pi/2$', r'$-\pi/4$', '0', r'$\pi/4$', r'$\pi/2$'])

fig.tight_layout()
fig.savefig('scattering-profile.pdf')

if 'batch' not in sys.argv:
    P.show()
