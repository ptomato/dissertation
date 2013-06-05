import numpy as N
from scipy.optimize import fmin


def refl_calc(kx, k0, eps0, eps1, eps2, d):
    k02 = N.array(k0 ** 2, dtype=complex)
    kx2 = N.array(kx ** 2)
    kz0 = N.sqrt(eps0 * k02 - kx2)
    kz1 = N.sqrt(eps1 * k02 - kx2)
    kz2 = N.sqrt(eps2 * k02 - kx2)
    kz0 = N.where(kz0.imag > 0, -kz0, kz0)
    kz1 = N.where(kz1.imag < 0, -kz1, kz1)
    kz2 = N.where(kz2.imag < 0, -kz2, kz2)
    z0 = kz0 / eps0
    z1 = kz1 / eps1
    z2 = kz2 / eps2
    r01 = (z0 - z1) / (z0 + z1)
    r12 = (z1 - z2) / (z1 + z2)
    delta = N.exp(2j * kz1 * d)
    r012 = (r01 + r12 * delta) / (1 + r01 * r12 * delta)
    return r01, r12, delta, r012


def refl_calc_3layer(kx, k0, eps0, eps1, eps2, eps3, d1, d2):
    k02 = N.array(k0 ** 2, dtype=complex)
    kx2 = N.array(kx ** 2)
    kz0 = N.sqrt(eps0 * k02 - kx2)
    kz1 = N.sqrt(eps1 * k02 - kx2)
    kz2 = N.sqrt(eps2 * k02 - kx2)
    kz3 = N.sqrt(eps3 * k02 - kx2)
    kz0 = N.where(kz0.imag > 0, -kz0, kz0)
    kz1 = N.where(kz1.imag < 0, -kz1, kz1)
    kz2 = N.where(kz2.imag < 0, -kz2, kz2)
    kz3 = N.where(kz3.imag < 0, -kz3, kz3)
    z0 = kz0 / eps0
    z1 = kz1 / eps1
    z2 = kz2 / eps2
    z3 = kz3 / eps3
    r01 = (z0 - z1) / (z0 + z1)
    r12 = (z1 - z2) / (z1 + z2)
    r23 = (z2 - z3) / (z2 + z3)
    delta1 = N.exp(2j * kz1 * d1)
    delta2 = N.exp(2j * kz2 * d2)
    d1d2 = delta1 * delta2
    denominator = (1.0 + r01 * r12 * delta1 + r12 * r23 * delta2
        + r01 * r23 * d1d2)
    r0123 = (r01 + r12 * delta1 + r01 * r12 * r23 * delta2
        + r23 * d1d2) / denominator
    return r01, delta1, r0123


def disp_rel(*args):
    r01, r12, delta, _ = refl_calc(*args)
    return 1.0 + r01 * r12 * delta


def disp_rel_pack(kx_pack, *args):
    retval = disp_rel(complex(*kx_pack), *args)
    return N.abs(retval)


def exact_numerical_nSP(k0, eps0, eps1, eps2, d, guess=None):
    if guess is None:
        guess = k0 * infinite_nSP(eps1, eps2)
    kx_solve = fmin(disp_rel_pack, N.array([guess.real, guess.imag]),
                    args=(k0, eps0, eps1, eps2, d),
                    disp=False)
    return complex(*kx_solve) / k0


def infinite_nSP(eps1, eps2):
    return N.sqrt(eps1 * eps2 / (eps1 + eps2))


def dip_minimum(kx, k0, eps0, eps1, eps2):
    r01, r12, _, _ = refl_calc(kx, k0, eps0, eps1, eps2, 0.0)
    kz1 = N.sqrt(eps1 * k0 ** 2 - kx ** 2)
    return -1j * N.log(-r01 / r12) / (2 * kz1)


def dip_minimum_solve(kx, *args):
    return N.abs(dip_minimum(kx, *args).imag)


def find_optimum_thickness(k0, eps0, eps1, eps2):
    kx_guess = k0 * infinite_nSP(eps1, eps2).real * 0.98
    kx, _, _, _, flag = fmin(dip_minimum_solve, kx_guess,
        args=(k0, eps0, eps1, eps2), disp=False, full_output=True)
    if flag != 0:
        thickness = N.nan
    else:
        thickness = dip_minimum(kx, k0, eps0, eps1, eps2).real
    return thickness
