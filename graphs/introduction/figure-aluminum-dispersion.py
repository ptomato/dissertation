import sys
sys.path.append('..')
import numpy as N
import plot_config
from tango import tango
from matplotlib import pyplot as P
from epsilons import epsilon_Al

min_wavelength, max_wavelength = 500e-9, 1200e-9

# Calculate with Drude-Lorentz model from Rakic et al.
wl_DL = N.linspace(min_wavelength, max_wavelength, 200)
e_DL = epsilon_Al(wl_DL)

# Calculate with tabulated data from Palik
_, wl_P_microns, nr_P, ni_P = N.loadtxt('Aluminum index data.csv',
    skiprows=3, delimiter=',', unpack=True)
mask = (wl_P_microns >= min_wavelength * 1e6) & (wl_P_microns <= max_wavelength * 1e6)
e_P = (nr_P[mask] + 1j * ni_P[mask]) ** 2

fig = P.figure()
ax = fig.gca()
real_DL, = ax.plot(wl_DL * 1e9, -e_DL.real, color=tango.skyblue3)
real_P, = ax.plot(wl_P_microns[mask] * 1e3, -e_P.real, 'o',
    color=tango.skyblue3, markeredgecolor=tango.skyblue3)
imag_DL, = ax.plot(wl_DL * 1e9, e_DL.imag, color=tango.scarletred3)
imag_P, = ax.plot(wl_P_microns[mask] * 1e3, e_P.imag, 'o',
    color=tango.scarletred3, markeredgecolor=tango.scarletred3)
ax.set_xlabel('Wavelength (nm)')
ax.set_ylabel('Dielectric constant (dimensionless)')
#ax.set_ylim(0, 1)

# Combine line artists for legend
ax.legend(((real_DL, real_P), (imag_DL, imag_P)),
    (r"$-\varepsilon'$", r"$\varepsilon''$"),
    numpoints=1, loc='best')

fig.tight_layout()

fig.savefig('bulk-aluminum-dispersion.pdf')
fig.savefig('bulk-aluminum-dispersion.png', dpi=150)

if 'batch' not in sys.argv:
    P.show()
