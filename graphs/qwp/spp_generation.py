"""Plasmon generation efficiency from fundamental slit mode
P. Lalanne, J. P. Hugonin, J. C. Rodier. (2006). "Approximate model for
surface-plasmon generation at slit apertures." JOSA A 23 (7), p. 1608."""

import numpy as N
from scipy import special


def I0_integrand(u, w):
    return N.sinc(N.outer(u, w)) ** 2


def I1_integrand(u, w, gamma):
    # The full integrand (weighted by sqrt(1 - u^2)) is singular at -1 and +1.
    # Adaptive QUADPACK quadrature and AdaptSim (Matlab's quad() function)
    # both fail on it for |x| > 1, presumably because there are poles close to
    # the real axis.
    # Gaussian quadrature succeeds. A fixed order of 200 seems to produce the
    # most accurate results balanced by computing time. However, the weighted
    # Gaussian quadrature from Lalanne's code works much faster.
    gamma_u = N.sqrt(N.asarray(1 - u ** 2, dtype=complex))
    wu = N.outer(u, w)
    return N.sinc(wu) * N.exp(-1j * N.pi * wu) / (gamma_u + gamma)[:, N.newaxis]


def lalanne_integral(func, order=20, *args):
    """Gaussian quadrature of a function, adapted from Lalanne's code.

    Computes integral of func(x, *args) / sqrt(1 - x^2) from -inf to +inf.
    Does this by splitting it up into two parts, [0, 1) and (1, inf].
    """
    points, weights = special.orthogonal.p_roots(order)
    # Points and weights for the first integral
    x1, w1 = (N. pi / 4) * (points + 1), (N.pi / 4) * weights
    # Points and weights for the second integral
    x2, w2 = (points + 1) / 2, weights / 2

    # for [0, 1), u = cos(x1)
    gauss1 = func(N.cos(x1), *args) + func(-N.cos(x1), *args)
    # for (1, inf], uu = sqrt(1 - uuu^2), uuu = 1 / x2 - 1
    uuu = 1 / x2 - 1
    uu = N.sqrt(uuu ** 2 + 1)
    gauss2 = (func(uu, *args) + func(-uu, *args)) \
        * (((uuu + 1) ** 2) / uu)[:, N.newaxis]

    return (w1[:, N.newaxis] * gauss1).sum(axis=0) \
        - 1j * (w2[:, N.newaxis] * gauss2).sum(axis=0)


def calc_I0(w_norm):
    """Calculate the I0 integral for normalized slit width w'."""
    return lalanne_integral(I0_integrand, 20, w_norm)


def calc_I1(w_norm, epsilon, n):
    """Calculate the I1 integral for normalized slit width w'.

    @w_norm: normalized slit width
    @epsilon: dielectric constant of metal
    @n: index of material on outside of slit"""
    gamma_SP = -N.sqrt(n ** 2 / (n ** 2 + epsilon))
    return lalanne_integral(I1_integrand, 120, w_norm, gamma_SP)


def interface_calculation(w, wl, epsilon, n1, n2, theta):
    """Surface-plasmon generation dynamics at a slit aperture.

    Returns r0, t0, alpha, beta
    @r0: Reflection coefficient from inside the slit to outside
    @t0: Transmission coefficient from outside the slit to inside
    @alpha: SP generation coefficient for illumination from the fundamental mode
      inside
    @beta: SP generation coefficient for illumation from a plane wave outside

    @w: slit width
    @wl: wavelength
    @n1: index of medium outside the slit
    @n2: index of medium inside the slit
    @theta: angle of incidence of plane wave"""
    w_norm = w * n1 / wl
    temp = (n1 / n2) * w_norm * calc_I0(w_norm)
    r0 = (temp - 1) / (temp + 1)

    alpha = (-1j * (1 - r0) * calc_I1(w_norm, epsilon, n1)
        * N.sqrt((w_norm * n1 ** 2 / (n2 * N.pi))
        * (N.sqrt(N.abs(epsilon)) / (-epsilon - n1 ** 2))))

    t0 = ((1 - r0) * N.sinc(w_norm * N.sin(theta))
        ) * N.sqrt(n1 / (n2 * N.cos(theta)))

    beta = -alpha * t0 / (1 - r0)

    return r0, t0, alpha, beta


def test_integrals():
    """Test our numerical integration by comparing it to Table 1 in the paper,
    which tabulates certain values"""
    import time

    bn = N.array([0.1, 0.3, 0.5, 0.7])
    epsilon = -26.27 + 1.85j

    I0_time = -time.clock()
    I0 = calc_I0(bn)
    I0_time += time.clock()
    I1_time = -time.clock()
    I1 = calc_I1(bn, epsilon, 1.0)
    I1_time += time.clock()

    print 'I0 took {0:.4} s'.format(I0_time)
    print 'I1 took {0:.4} s'.format(I1_time)

    I0_ref = N.array([3.09 - 4.09j, 2.72 - 1.68j, 2.13 - .63j, 1.54 - .18j])
    I1_ref = N.array([.53 - 2.93j,  1.75 - 1.8j,  1.79 - .4j,  1.01 + .35j])
    dI0 = N.abs(I0_ref - I0) / N.abs(I0_ref)
    dI1 = N.abs(I1_ref - I1) / N.abs(I1_ref)

    print 'Table 1. I1 and I0 for Gold at 800 nm (epsilon=-26.27+1.85i)'
    print " w' {0[0]:10.2} {0[1]:10.2} {0[2]:10.2} {0[3]:10.2}".format(bn)
    print ' I0 {0[0]:10.2f} {0[1]:10.2f} {0[2]:10.2f} {0[3]:10.2f}'.format(I0)
    print 'dI0 {0[0]:10.0%} {0[1]:10.0%} {0[2]:10.0%} {0[3]:10.0%}'.format(dI0)
    print ' I1 {0[0]:10.2f} {0[1]:10.2f} {0[2]:10.2f} {0[3]:10.2f}'.format(I1)
    print 'dI1 {0[0]:10.0%} {0[1]:10.0%} {0[2]:10.0%} {0[3]:10.0%}'.format(dI1)

if __name__ == '__main__':
    test_integrals()
