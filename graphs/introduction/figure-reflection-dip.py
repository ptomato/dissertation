import sys
sys.path.append('..')
import numpy as N
import plot_config
from tango import tango
from matplotlib import pyplot as P
from epsilons import epsilon_Al

min_wavelength, max_wavelength = 200e-9, 2000e-9
percentage_formatter = P.FormatStrFormatter('%i%%')

# Calculate with Drude-Lorentz model from Rakic et al.
wl_DL = N.linspace(min_wavelength, max_wavelength, 200)
n_Al_DL = N.sqrt(epsilon_Al(wl_DL))
R_DL = N.abs((1 - n_Al_DL) / (1 + n_Al_DL)) ** 2

# Calculate with tabulated data from Palik
_, wl_P_microns, nr_P, ni_P = N.loadtxt('Aluminum index data.csv',
    skiprows=3, delimiter=',', unpack=True)
mask = (wl_P_microns >= min_wavelength * 1e6) & (wl_P_microns <= max_wavelength * 1e6)
n_Al_P = nr_P[mask] + 1j * ni_P[mask]
R_P = N.abs((1 - n_Al_P) / (1 + n_Al_P)) ** 2

fig = P.figure()
ax = fig.gca()

# Create rainbow
ncolors = 50
rainbow_data = N.linspace(0, 1, ncolors)[N.newaxis, :]
rainbow_wavelengths = N.linspace(380.0, 750.0, ncolors)
ax.pcolor(rainbow_wavelengths, N.array([0, 100]), rainbow_data,
    cmap='spectral', alpha=0.2, edgecolor='none')

ax.plot(wl_DL * 1e9, R_DL * 100, color='black', label=u'Raki\N{Latin small letter c with acute} et al. (1998)')
ax.plot(wl_P_microns[mask] * 1e3, R_P * 100, 'o', color='black', label='Palik')
ax.set_xlabel('Wavelength (nm)')
ax.set_ylabel('Reflectance')
ax.set_ylim(0, 100)
ax.yaxis.set_major_formatter(percentage_formatter)
fig.tight_layout()

# Add zoom indicator
coordinates = N.array([817, 12.6, 650, 86, 650, 92, 950, 92, 1872, 74.4])
patch = P.Polygon(coordinates.reshape(-1, 2), closed=True,
    linewidth=0, facecolor=tango.aluminum3, alpha=0.5)
ax.add_patch(patch)

ax = fig.add_axes([0.4, 0.25, 0.5, 0.5])
ax.plot(wl_DL * 1e9, R_DL * 100, color='black')
ax.plot(wl_P_microns[mask] * 1e3, R_P * 100, 'o', color='black')
ax.set_xlim(650, 950)
ax.set_ylim(86, 92)
ax.yaxis.set_major_formatter(percentage_formatter)

fig.savefig('aluminum-dip.pdf')
fig.savefig('aluminum-dip.png', dpi=150)

if 'batch' not in sys.argv:
    P.show()
