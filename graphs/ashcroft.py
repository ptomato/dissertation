import numpy as N
from scipy import constants as Const
from crystal_plane import CrystalPlane
"""
Parallel-band conductivity (Ashcroft & Sturm, 1971) using measured data and
fits (Mathewson & Myers, 1972)
"""

# sigma_a: Ashcroft & Sturm's "convenient" unit of conductivity
sigma_a = Const.e ** 2 / (24 * N.pi * Const.value('Bohr radius') * Const.hbar)
sigma_CGS = Const.c ** 2.0 * 1e-7   # Multiply S/m by sigma_CGS to get 1/s
# sigma_a * sigma_CGS should equal 5.48e14 1/s (misprint in paper: 5.48e-14 1/s)
N.testing.assert_approx_equal(sigma_a * sigma_CGS, 5.48e14, significant=3)

# Mathewson & Myers (1972) temperature-dependent data
# 4.2 K: U111, U200, tau_d, tau_pb, sigma_dc from Benbow & Lynch (1975)
# other parameters at 4.2 K are Mathewson & Myers' extrapolated values for 0 K
mm_temp     = N.array([4.2,   198.0, 298.0, 404.0, 552.0])
mm_a        = N.array([4.032, 4.041, 4.050, 4.060, 4.076]) * 1e-10  # m
mm_k_fermi  = N.array([.9273, .9252, .9232, .9209, .9173]) / Const.value('Bohr radius')
mm_U111     = N.array([0.218, 0.208, 0.190, 0.166, 0.165]) * Const.eV
mm_U200     = N.array([0.802, 0.763, 0.738, 0.699, 0.659]) * Const.eV
mm_m0       = N.array([1.56,  1.51,  1.48,  1.43,  1.41])
mm_tau_d    = N.array([11.0,  11.8,  10.2,  6.2,   5.2]) * 1e-15    # s
mm_tau_pb   = N.array([6.09,  4.9,   3.8,   3.1,   2.2]) * 1e-15    # s
mm_sigma_dc = N.array([3.25,  3.58,  3.14,  1.96,  1.65]) * 1e17 / sigma_CGS
P200        = N.array([0.985, 0.956, 0.933, 0.898, 0.835])
P111        = N.array([.9887, .9654, .9593, .9166, .865])

# Plasma frequency:
#print N.sqrt(mm_sigma_dc / (mm_tau_d * Const.epsilon_0)) * Const.hbar / Const.eV


def pb_absorption_energy_range(plane, a, m0, k_fermi, U):
    """
    Return the range of energies within which parallel-band absorption takes
    place; it starts at twice the pseudopotential, and ends at the point where
    the upper band crosses the Fermi energy (?)
    @plane: a CrystalPlane instance
    @a: lattice constant in m
    @m0: mass ratio
    @k_fermi: fermi wave vector in 1/m
    @U: crystal plane pseudopotential in J
    """
    K = plane.magnitude_factor / a
    energy_K = (Const.hbar * K) ** 2 / (2 * m0 * Const.m_e)
    hbar_omega0 = energy_K * (2 * k_fermi / K - 1)

    return 2 * U, hbar_omega0


def horrible_function(z, b, t0, rho, phi):
    """J(omega) from Ashcroft & Sturm (1971)"""
    # Calculation shortcuts
    z2b2 = (z ** 2 - b ** 2) / (z ** 2 + b ** 2)
    zb2 = 2 * z * b / (z ** 2 + b ** 2)
    sphi, cphi = N.sin(phi), N.cos(phi)

    J1 = 2 * zb2 * rho * N.arctan(t0)
    J2 = (0.5 * (cphi * z2b2 + sphi * zb2)
          * N.log((t0 ** 2 + 2 * t0 * rho * sphi + rho ** 2) /
                  (t0 ** 2 - 2 * t0 * rho * sphi + rho ** 2)))
    J3 = ((sphi * z2b2 - cphi * zb2)
          * (N.arctan2(t0 + rho * sphi, rho * cphi) +
             N.arctan2(t0 - rho * sphi, rho * cphi)))
    return (J1 + J2 + J3) / N.pi


def imaginary_horrible_function(z, b, t0, rho, phi1, phi2):
    sphi1, cphi1 = N.sin(phi1), N.cos(phi1)

    J1 = 0.5 * sphi1 * N.log((t0 ** 2 + 2 * t0 * rho * cphi1 + rho ** 2) /
                             (t0 ** 2 - 2 * t0 * rho * cphi1 + rho ** 2))
    J2 = cphi1 * (N.arctan2(t0 + rho * cphi1, rho * sphi1) +
                  N.arctan2(t0 - rho * cphi1, rho * sphi1))
    J3 = (N.pi * ((b ** 2 - z ** 2) / (z ** 2 + b ** 2))
        * horrible_function(z, b, t0, rho, phi2))
    return (J1 + J2 + J3) / (2 * b * N.pi * rho)


def parallel_band_conductivity(frequency, plane, a, m0, k_fermi, U, tau):
    """
    Return the contribution to the optical conductivity resulting from
    parallel-band absorption in a certain plane.
    @frequency: frequency in Hz
    @plane: a CrystalPlane instance
    @a: lattice constant in m
    @m0: mass ratio
    @k_fermi: fermi wave vector in 1/m
    @U: crystal plane pseudopotential in J
    @tau: parallel-band relaxation time in s
    """
    K = plane.magnitude_factor / a

    energy_low, energy_high = pb_absorption_energy_range(plane, a, m0, k_fermi, U)
    energy = Const.hbar * frequency
    damping_energy = Const.hbar / tau

    z = energy / energy_low
    z0 = energy_high / energy_low
    t0 = N.sqrt(z0 ** 2 - 1.0)

    # "To obtain the total absorption corresponding to the entire first zone
    # we simply weight these results by the appropriate number of planes
    # bounding the zone."
    factor = plane.multiplicity * sigma_a * Const.value('Bohr radius') * K

    b = damping_energy / energy_low
    rho = ((1 + b ** 2 - z ** 2) ** 2 + (2 * b * z) ** 2) ** 0.25
    phi1 = 0.5 * (0.5 * N.pi + N.arctan2(1 + b ** 2 - z ** 2, 2 * b * z))
    phi2 = 0.5 * (0.5 * N.pi - N.arctan2(1 + b ** 2 - z ** 2, 2 * b * z))
    realpart = (((z / rho) / (z ** 2 + b ** 2))
        * horrible_function(z, b, t0, rho, phi2))
    imagpart = imaginary_horrible_function(z, b, t0, rho, phi1, phi2)

    return factor * (realpart - 1j * imagpart)


def drude_conductivity(frequency, sigma_dc, tau_d):
    """
    Return the ideal Drude conductivity as a function of @frequency in Hz,
    given the parameters @sigma_dc, conductivity at frequency 0 in S/m, and
    @tau_d, relaxation time in s.
    """
    return sigma_dc / (1 - 1j * tau_d * frequency)


def conductivity(frequency, temperature_index=None, temperature=300.0,
    include_parallel_band=True, **kw):
    """
    Return the total optical conductivity, consisting of the Drude conductivity
    plus the contribution from the parallel-band absorption in the {111} and
    {200} planes. Also returns a tuple of the model parameters used: (a,
    k_fermi, U111, U200, m0, tau_d, tau_pb, sigma_dc).

    Pass @temperature_index to use fitted data from Mathewson & Myers (1972);
    it corresponds to the following temperatures:
    0 - 198 K
    1 - 298 K
    2 - 404 K
    3 - 552 K

    If you do not pass @temperature_index, then the function will attempt to
    estimate (by interpolation or extrapolation) parameters for @temperature
    (in K).

    Passing @include_parallel_band = False will leave out the parallel-band
    resonances, only including the Drude conductivity.

    You can pass any of the parameters as keyword arguments (a, k_fermi, U111,
    U200, m0, tau_d, tau_pb, sigma_dc) to override them.
    """

    if temperature_index is not None:
        index = temperature_index + 1  # don't use incomplete data for 0 K
        a = mm_a[index]
        k_fermi = mm_k_fermi[index]
        U111 = mm_U111[index]
        U200 = mm_U200[index]
        m0 = mm_m0[index]
        tau_d = mm_tau_d[index]
        tau_pb = mm_tau_pb[index]
        sigma_dc = mm_sigma_dc[index]
    else:
        a_fit = N.polyfit(mm_temp, mm_a, 2)
        a = N.polyval(a_fit, temperature)
        kf_fit = N.polyfit(mm_temp, mm_k_fermi, 2)
        k_fermi = N.polyval(kf_fit, temperature)
        U200_0 = 0.789 * Const.eV  # mean values from Mathewson & Myers (1972)
        U111_0 = 0.1965 * Const.eV
        P200_fit = N.polyfit(mm_temp, P200, 2)
        U200 = U200_0 * N.polyval(P200_fit, temperature)
        P111_fit = N.polyfit(mm_temp, P111, 2)
        U111 = U111_0 * N.polyval(P111_fit, temperature)
        m0_fit = N.polyfit(mm_temp, mm_m0, 1)
        m0 = N.polyval(m0_fit, temperature)
        tau_d_fit = N.polyfit(mm_temp, mm_tau_d, 1)
        tau_d = N.polyval(tau_d_fit, temperature)
        tau_pb_fit = N.polyfit(mm_temp, mm_tau_pb, 1)
        tau_pb = N.polyval(tau_pb_fit, temperature)
        sigma_dc_fit = N.polyfit(mm_temp, mm_sigma_dc, 1)
        sigma_dc = N.polyval(sigma_dc_fit, temperature)

    # Override parameters with keyword arguments if given
    a = kw.get('a', a)  # second argument is default value
    k_fermi = kw.get('k_fermi', k_fermi)
    U111 = kw.get('U111', U111)
    U200 = kw.get('U200', U200)
    m0 = kw.get('m0', m0)
    tau_d = kw.get('tau_d', tau_d)
    tau_pb = kw.get('tau_pb', tau_pb)
    sigma_dc = kw.get('sigma_dc', sigma_dc)

    if include_parallel_band:
        p200 = CrystalPlane(2, 0, 0)
        p111 = CrystalPlane(1, 1, 1)
        conductivity = (drude_conductivity(frequency, sigma_dc, tau_d)
            + parallel_band_conductivity(frequency, p200, a, m0, k_fermi, U200, tau_pb)
            + parallel_band_conductivity(frequency, p111, a, m0, k_fermi, U111, tau_pb))
    else:
        conductivity = drude_conductivity(frequency, sigma_dc, tau_d)
    return conductivity, (a, k_fermi, U111, U200, m0, tau_d, tau_pb, sigma_dc)


def epsilon_Al_temp(frequency, *args, **kw):
    full_output = kw.pop('full_output', False)
    sigma, parameters = conductivity(frequency, *args, **kw)
    epsilon = 1 + (1j * sigma / (frequency * Const.epsilon_0))
    if full_output:
        return epsilon, parameters
    return epsilon
