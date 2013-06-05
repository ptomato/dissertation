# coding: utf8

import warnings
import numpy as N
from scipy import constants as Const

################################################################################
## METALS

# Model validity constraints in eV
limits = {
    'Ag': (0.125, 6.0),
    'Au': (0.125, 6.0),
    'Cu': (0.1, 6.0),
    'Al': (6.2e-3, 10e3),
    'Be': (0.06, 26.0),
    'Cr': (0.069, 5.0),
    'Ni': (0.2, 5.0),
    'Pd': (0.1, 6.0),
    'Pt': (0.1, 5.0),
    'Ti': (0.06, 2.6),
    'W': (0.1, 5.0)
}

# Plasma frequency in eV
plasma_frequency = {
    'Ag': 9.01,
    'Au': 9.03,
    'Cu': 10.83,
    'Al': 14.98,
    'Be': 18.51,
    'Cr': 10.75,
    'Ni': 15.92,
    'Pd': 9.72,
    'Pt': 9.59,
    'Ti': 7.29,
    'W':  13.22
}

resonance_strength = {
    'Ag': [0.845, 0.065, 0.124, 0.011, 0.840, 5.646],
    'Au': [0.760, 0.024, 0.010, 0.071, 0.601, 4.384],
    'Cu': [0.575, 0.061, 0.104, 0.723, 0.638],
    'Al': [0.523, 0.227, 0.050, 0.166, 0.030],
    'Be': [0.084, 0.031, 0.140, 0.530, 0.130],
    'Cr': [0.168, 0.151, 0.150, 1.149, 0.825],
    'Ni': [0.096, 0.100, 0.135, 0.106, 0.729],
    'Pd': [0.330, 0.649, 0.121, 0.638, 0.453],
    'Pt': [0.333, 0.191, 0.659, 0.547, 3.576],
    'Ti': [0.148, 0.899, 0.393, 0.187, 0.001],
    'W':  [0.206, 0.054, 0.166, 0.706, 2.590]
}

damping_frequency = {
    'Ag': [0.048, 3.886, 0.452, 0.065, 0.916, 2.419],
    'Au': [0.053, 0.241, 0.345, 0.870, 2.494, 2.214],
    'Cu': [0.030, 0.378, 1.056, 3.213, 4.305],
    'Al': [0.047, 0.333, 0.312, 1.351, 3.382],
    'Be': [0.035, 1.664, 3.395, 4.454, 1.802],
    'Cr': [0.047, 3.175, 1.305, 2.676, 1.335],
    'Ni': [0.048, 4.511, 1.334, 2.178, 6.292],
    'Pd': [0.008, 2.950, 0.555, 4.621, 3.236],
    'Pt': [0.080, 0.517, 1.838, 3.668, 8.517],
    'Ti': [0.082, 2.276, 2.518, 1.663, 1.762],
    'W':  [0.064, 0.530, 1.281, 3.332, 5.836]
}

resonance_frequency = {
    'Ag': [0.0, 0.816, 4.481, 8.185, 9.083, 20.29],
    'Au': [0.0, 0.415, 0.830, 2.969, 4.304, 13.32],
    'Cu': [0.0, 0.291, 2.957, 5.300, 11.18],
    'Al': [0.0, 0.162, 1.544, 1.808, 3.473],
    'Be': [0.0, 0.100, 1.032, 3.183, 4.604],
    'Cr': [0.0, 0.121, 0.543, 1.970, 8.775],
    'Ni': [0.0, 0.174, 0.582, 1.597, 6.089],
    'Pd': [0.0, 0.336, 0.501, 1.659, 5.715],
    'Pt': [0.0, 0.780, 1.314, 3.141, 9.249],
    'Ti': [0.0, 0.777, 1.545, 2.509, 19.43],
    'W':  [0.0, 1.004, 1.917, 3.580, 7.498]
}


def _wavelength_to_frequency(wl):
    return 2 * N.pi * Const.c / wl


def _check_limits(inp, lower, upper, substance):
    inp_array = N.asanyarray(inp)
    if N.any((inp_array < lower) | (inp_array > upper)):
        warnings.warn('Wavelength is outside of model validity range for {}'
            .format(substance))


def _drude_lorentz(metal, wavelength):
    """Drude-Lorentz model of epsilon

    Reference: Rakic, Djurisic, Elazar, & Majewski (1998). Optical properties of
    metallic films for vertical-cavity optoelectronic devices. Applied Optics 37
    (22), 5271."""

    frequency = _wavelength_to_frequency(wavelength)

    hf_eV = Const.hbar * frequency / Const.eV
    _check_limits(hf_eV, limits[metal][0], limits[metal][1], metal)

    # Plasma frequency (rad/s)
    Omega_p = plasma_frequency[metal] * Const.eV / Const.hbar

    retval = N.ones_like(frequency, dtype=complex)
    parameters = zip(
        resonance_strength[metal],
        N.array(damping_frequency[metal]) * Const.eV / Const.hbar,
        N.array(resonance_frequency[metal]) * Const.eV / Const.hbar)
    for f, Gamma, omega in parameters:
        retval += (f * Omega_p ** 2) / ((omega ** 2 - frequency ** 2)
            - 1.0j * Gamma * frequency)

    return retval


def _make_metal_function(metal):
    retval = lambda x: _drude_lorentz(metal, x)
    retval.__doc__ = """
    Dielectric constant of {}, valid from {:.0f} to {:.0f} nm.
    Source: Rakic, Djurisic, Elazar, & Majewski (1998). Optical properties of
    metallic films for vertical-cavity optoelectronic devices. Applied Optics 37
    (22), 5271.""".format(
        metal,
        1240.0 / limits[metal][1],
        1240.0 / limits[metal][0])
    return retval

epsilon_Ag = _make_metal_function('Ag')
epsilon_Au = _make_metal_function('Au')
epsilon_Cu = _make_metal_function('Cu')
epsilon_Al = _make_metal_function('Al')
epsilon_Be = _make_metal_function('Be')
epsilon_Cr = _make_metal_function('Cr')
epsilon_Ni = _make_metal_function('Ni')
epsilon_Pd = _make_metal_function('Pd')
epsilon_Pt = _make_metal_function('Pt')
epsilon_Ti = _make_metal_function('Ti')
epsilon_W = _make_metal_function('W')

################################################################################
## DIELECTRICS


def _sellmeier(wavelength, *args):
    """Sellmeier equation with N terms. constants must be 2*N in length."""
    assert len(args) % 2 == 0
    l2 = (wavelength * 1e6) ** 2
    epsilon = 1.0
    for A, B in zip(args[0::2], args[1::2]):
        epsilon += A * l2 / (l2 - B ** 2)
    return epsilon


def epsilon_BK7(wavelength):
    """
    Dielectric constant of BK7 glass, valid from 300 to 2500 nm
    Source: SCHOTT. Optical Glass Data Sheets.
    2008-02-26 (via www.refractiveindex.info)
    Wavelength in meters
    """
    _check_limits(wavelength, 3e-7, 2.5e-6, 'BK7')
    return _sellmeier(wavelength,
        1.03961212,  N.sqrt(0.00600069867),
        0.231792344, N.sqrt(0.0200179144),
        1.01046945,  N.sqrt(103.560653))


def epsilon_Si3N4(wavelength):
    """
    Dielectric function of silicon nitride. From: T. Bååk (1982).
    "Silicon oxynitride; a material for GRIN optics."
    Appl. Opt. 21 (6), 1069. Author refers to another paper behind a
    paywall: H. R. Philipp (1973). "Optical properties of silicon
    nitride." J. Electrochem. Soc. 120 (2), pp. 295-300.
    Wavelength in meters. Unknown validity range.
    """
    return _sellmeier(wavelength, 2.8939, 139.67e-3)


def epsilon_Al2O3(wavelength):
    """
    Dielectric constant of α-aluminum oxide, 250-900 nm.
    Fit to SOPRA data by Babeva, Kitova, Mednikarov, & Konstantinov
    (2002). Appl. Opt. 41 (19), 3840.
    Wavelength in meters
    """
    _check_limits(wavelength, 2.5e-7, 9e-7, 'Al2O3')
    A = 1.7088
    B = 97.626
    return 1.0 + A / (1 - (B / (wavelength * 1e9)) ** 2)


def epsilon_a_Al2O3(wavelength):
    """Drude-Lorentz model of epsilon for amorphous aluminum oxide, from 10000
    to 33333 nm. (300 to 1000 cm^-1.)

    Reference: Y. T. Chu, J. B. Bates, C. W. White, G. C. Farlow (1988).
    Optical dielectric functions for amorphous-Al2O3 and gamma-Al2O3.
    J. Appl. Phys 64 (7), 3727."""

    wavenumber = 0.01 / wavelength
    _check_limits(wavenumber, 300.0, 1000.0, 'amorphous Al2O3')

    frequency = 2.0 * N.pi * Const.c / wavelength

    # High-frequency limit
    eps_inf = 2.8
    # Strength
    strg = N.array([3.75, 1.46])
    # Resonance frequency (given in 1/cm)
    resf = 200.0 * N.pi * Const.c * N.array([422.0, 721.0])
    # Damping frequency (given as a fraction of resonance frequency)
    damp = 200.0 * N.pi * Const.c * N.array([0.402 * 422.0, 0.245 * 721.0])

    retval = N.ones_like(frequency, dtype=complex) * eps_inf
    for f, gam, omega in zip(strg, damp, resf):
        retval += (f * omega ** 2) / ((omega ** 2 - frequency ** 2)
                                        - 1j * gam * frequency)
    return retval


def epsilon_FS(wavelength):
    """
    Dielectric function of silicon dioxide (fused silica). From
    I. H. Malitson (1965). "Interspecimen comparison of the refractive
    index of fused silica." J. Opt. Soc. Am. 55 (10), pp. 1205-1208
    via refractiveindex.info.
    Wavelength in meters. Valid from 210 to 3710 nm at 20 degrees C.
    """
    _check_limits(wavelength, 2.1e-7, 3.71e-6, 'FS')
    return _sellmeier(wavelength,
        0.6961663, 0.0684043,
        0.4079426, 0.1162414,
        0.8974794, 9.896161)


def epsilon_SF57HHT(wavelength):
    """
    Dielectric function of Schott SF57HHT glass (example high-index glass).
    From refractiveindex.info. Wavelength in meters. Unknown validity range.
    """
    return _sellmeier(wavelength,
        1.81651371,  N.sqrt(0.0143704198),
        0.428893641, N.sqrt(0.0592801172),
        1.07186278,  N.sqrt(121.419942))


def epsilon_MgF2(wavelength, ray='o'):
    """
    Dielectric function of magnesium fluoride. From M. J. Dodge (1984).
    "Refractive properties of magnesium fluoride." Appl. Opt. 23 (12),
    pp.1980-1985 via refractiveindex.info.
    Wavelength in meters. Valid from 200 to 7000 nm.
    """
    _check_limits(wavelength, 2e-7, 7e-6, 'MgF2')
    if ray.startswith('o'):
        # Ordinary ray
        return _sellmeier(wavelength,
            0.48755108, 0.04338408,
            0.39875031, 0.09461442,
            2.3120353,  23.793604)
    elif ray.startswith('e'):
        # Extraordinary ray
        return _sellmeier(wavelength,
            0.41344023, 0.03684262,
            0.50497499, 0.09076162,
            2.4904862,  23.771995)
    else:
        raise ValueError('Please specify ordinary or extraordinary ray')


def epsilon_GGG(wavelength, T=None):
    """
    Dielectric function of gadolinium gallium garnet. From D. L. Wood &
    K. Nassau (1990). "Optical properties of gadolinium gallium garnet." Appl.
    Opt. 29 (25), pp. 3704-3707.
    Wavelength in meters. Valid from 360 to 6000 nm.
    T is the temperature in K (use None for room temperature.) Temperatures
    other than room temperature are only approximately valid from 360 to
    1800 nm.
    """
    _check_limits(wavelength, 3.6e-7, 6e-6, 'GGG')
    epsilon = _sellmeier(wavelength,
        1.7727, 0.1567,
        0.9767, 0.01375,
        4.9668, 22.715)
    if T is None:
        return epsilon
    _check_limits(wavelength, 3.6e-7, 1.8e-6, 'GGG at temperature')
    dndT = 1.69e-5 + 0.06e-5 / (wavelength * 1e6) ** 3
    n = N.sqrt(epsilon) + (dndT * (T - 298))
    return n ** 2


def epsilon_F2(wavelength):
    """
    Dielectric function of F2 glass, a lead-containing glass type. From
    refractiveindex.info.
    """
    _check_limits(wavelength, 3e-7, 2.5e-6, 'F2')
    return _sellmeier(wavelength,
        1.34533359, N.sqrt(.00997743871),
        .209073176, N.sqrt(.0470450767),
        .937357162, N.sqrt(111.886764))

if __name__ == '__main__':
    wl = 800e-9
    print N.sqrt(epsilon_F2(wl))
