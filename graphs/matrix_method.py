import numpy as N
from local_extrema import detect_local_minima


def create_eigenvalue_grid(rmin, rmax, imin, imax, k0, npoints=200):
    """
    Use broadcasting to create a matrix of possible kSP values.
    @rmin, @rmax: real part of effective SP index
    @imin, @imax: imaginary part of effective SP index
    """
    kr = N.linspace(rmin * k0, rmax * k0, npoints)
    ki = N.linspace(imin * k0, imax * k0, npoints - 1)
    # take -1 so that the dimensions are not equal - this will raise a
    # broadcasting error if we get the dimensions mixed up, hopefully
    kSP = (kr[:, N.newaxis] + 1j * ki[N.newaxis, :])
    return kr, ki, kSP


def calc_eigenvalue_matrix(k0, eps, d, kSP):
    """
    Calculate the matrix element M22 which must be 0.
    """
    # Calculate kz in each layer
    kz = N.sqrt(eps * k0 ** 2 - kSP[..., N.newaxis] ** 2)
    # Choose the sign of kz so that the imaginary part is positive
    kz = N.where(kz.imag < 0, -kz, kz)
    kz[..., 0] *= -1

    # Pre-calculate the first matrix multiplication for the first interface
    matrix_shape = (kSP.shape[0], kSP.shape[1], 2, 2)
    M0 = N.ones(matrix_shape, dtype=complex)
    z0 = kz[..., 0] / eps[0]
    z1 = kz[..., 1] / eps[1]
    r10 = (z1 - z0) / (z1 + z0)
    t10 = 1 + r10
    M0[..., 1, 0] = r10
    M0[..., 0, 1] = r10
    M0 /= t10[..., N.newaxis, N.newaxis]
    del z0, z1, r10, t10

    # Iterate over the following layers
    for dn, en, kzn, zn1 in zip(d, eps[1:-1],
                                  N.rollaxis(kz[..., 1:-1], 2),
                                  N.rollaxis(kz[..., 2:] / eps[2:], 2)):
        M1 = N.empty_like(M0)
        zn = kzn / en
        rn1n = (zn1 - zn) / (zn1 + zn)
        tn1n = 1 + rn1n
        kd = 1j * kzn * dn
        dplus = N.exp(kd)
        dminus = N.exp(-kd)
        M1[..., 0, 0] = dplus
        M1[..., 1, 0] = rn1n * dplus
        M1[..., 0, 1] = rn1n * dminus
        M1[..., 1, 1] = dminus
        M1 /= tn1n[..., N.newaxis, N.newaxis]
        del kd, dplus, dminus, rn1n, zn, tn1n
        # Matrix multiplication over the last two axes
        M0 = N.einsum('...ij,...jk->...ik', M1, M0)
        del M1

    return M0


def dispersion_relation(wavelengths, epsilon_functions, thicknesses, modenum=0,
    bounds=(1.0, 1.1, 0.0001, 0.1)):
    indices = N.empty_like(wavelengths, dtype=complex)
    xmin, xmax, ymin, ymax = bounds

    for ix, wl in enumerate(wavelengths):
        epsilons = N.array([e(wl) for e in epsilon_functions])
        k0 = 2 * N.pi / wl

        kr, ki, kSP = create_eigenvalue_grid(xmin, xmax, ymin, ymax, k0)
        q = calc_eigenvalue_matrix(k0, epsilons, thicknesses, kSP)[..., 1, 1]
        min_indices = detect_local_minima(abs(q))
        # Remove minima that are on the left or bottom edge
        min_indices = map(N.array,
            zip(*[(x, y) for (x, y) in zip(*min_indices) if all((x, y))]))
        modes = (kr[min_indices[0]] + 1j * ki[min_indices[1]]) / k0
        mode = modes[modenum]

        # Recalculate, but with a finer grid
        kr, ki, kSP = create_eigenvalue_grid(mode.real - 1e-3,
            mode.real + 1e-3, mode.imag - 1e-3, mode.imag + 1e-3, k0)
        q = calc_eigenvalue_matrix(k0, epsilons, thicknesses, kSP)[..., 1, 1]
        min_indices = detect_local_minima(abs(q))
        modes = (kr[min_indices[0]] + 1j * ki[min_indices[1]]) / k0
        mode = modes[0]

        indices[ix] = mode

    return indices


def calc_eigenmode(k0, eps, d, mode, tail=1e-7, npoints=100):
    """
    Calculate the complex magnetic field amplitude of the eigenmode.
    @tail: Distance to show in the infinite border layers (nm)
    """
    A = N.zeros((eps.shape[0], 2), dtype=complex)
    A[0, 1] = 1.0
    A[1, 1] = 1.0

    kzmode = k0 * N.sqrt(eps - mode ** 2)
    kzmode = N.where(kzmode.imag < 0, -kzmode, kzmode)
    kzmode[0] *= -1

    for ix, (en, kzn, zn1) in \
        enumerate(zip(eps[:-1], kzmode[:-1], kzmode[1:] / eps[1:])):

        if ix != 0:
            M0 = N.zeros((2, 2), dtype=complex)
            kd = 1j * kzn * d[ix - 1]
            M0[0, 0] = N.exp(kd)[0]  # [0]: workaround for http://comments.gmane.org/gmane.comp.python.numeric.general/43850
            M0[1, 1] = N.exp(-kd)[0]
            del kd
            A[ix + 1, :] = N.dot(M0, A[ix, :])
            del M0

        M0 = N.ones((2, 2), dtype=complex)
        zn = kzn / en
        rn1n = (zn1 - zn) / (zn1 + zn)
        tn1n = 1 + rn1n
        M0[1, 0] = rn1n[0]
        M0[0, 1] = rn1n[0]
        M0 /= tn1n
        del zn, rn1n, tn1n
        A[ix + 1, :] = N.dot(M0, A[ix + 1, :])
        del M0

    dn = d.sum()
    z = N.linspace(-tail, tail + dn, npoints)
    Hy = N.zeros_like(z, dtype=complex)

    # Exponential tails in the outside layers
    Hy[z < 0.0] = A[00, 1] * N.exp(1j * kzmode[00] * (z - 00))[z < 0.0]
    Hy[z >= dn] = A[-1, 0] * N.exp(1j * kzmode[-1] * (z - dn))[z >= dn]

    for ix, zn in enumerate(d.cumsum()):
        z0 = zn - d[ix]
        z_layer = z[(z >= z0) & (z < zn)] - z0
        Hy[(z >= z0) & (z < zn)] = \
            (A[ix + 1, 0] * N.exp(+1j * kzmode[ix + 1] * z_layer) +
             A[ix + 1, 1] * N.exp(-1j * kzmode[ix + 1] * z_layer))

    return z, Hy
