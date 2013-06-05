import os.path
import glob
import re
import numpy as N
from scipy import signal, special, fftpack
from scipy.ndimage import filters, morphology


# These functions numerically solve the two-dimensional diffraction integral in
# its convolution form. h(x, z) is the convolution kernel.

def h(x, z, k):
    r2 = x ** 2 + z ** 2
    return (z * (1 - 1j) * N.exp(1j * k * N.sqrt(r2)) * r2 ** -0.75
        / N.sqrt(4 * N.pi / k.real))


def diffract(U0, x, z, k, res):
    '''Calculate the diffraction pattern of field @U0 at a distance @z.
    @x contains the position of each point in @U0.'''
    # The discrete convolution algorithm assumes the sampling interval is 1, so
    # this is why we scale the answer by 'res'.
    return signal.fftconvolve(U0, h(x, z, k), mode='same') * res


def grid(width, resolution):
    '''Create 2-D grids of coordinates, Cartesian and polar. The grid is square,
    with @width the length of each side, and @resolution the width of each
    element. Returns four equally-sized arrays, containing the x, y, r, and
    theta coordinates.'''

    range = N.arange(-width / 2, width / 2, resolution)
    x, y = N.meshgrid(range, range)
    r, theta = N.hypot(x, y), N.arctan2(y, x)

    return x, y, r, theta


def I2(a, z):
    zz = N.array(z, dtype=complex)
    return special.iv(a - 0.5, zz) - special.iv(a + 0.5, zz)


def vortex_beam(r, theta, Q, w0):
    '''Returns the far field of a Gaussian with a spiral phase imprinted on it, with vortex
    charge @Q. The field is normalized so that max(|E|) = 1. @w0 is a width parameter of the
    vortex, but is not equal to the 1/e^2 width of the original Gaussian.'''

    rho = r / w0
    retval = rho * N.exp(1.0j * Q * theta - rho ** 2) * I2(0.5 * Q, rho ** 2)
    return retval / retval.max()


def vortex_beam_by_fourier(r, theta, Q, w0):
    '''
    Spiral phase plate with vorticity Q
    Calculated by Fourier transform - not exact
    r and theta must be square
    '''

    # The original function
    F0 = N.exp(-r ** 2 / w0 ** 2 + 1.0j * Q * theta)
    oldsize = F0.shape[0]

    # Pad it with large amounts of zeros
    padding = N.zeros_like(F0)
    inarray = N.vstack((
        N.hstack((padding, padding, padding)),
        N.hstack((padding, F0,      padding)),
        N.hstack((padding, padding, padding))
        ))
    insize = inarray.shape[0]

    # Do the Fourier transform
    FF = fftpack.fftshift(fftpack.fft2(fftpack.ifftshift(inarray)))
    FF = FF[int((insize - oldsize) / 2):int((insize + oldsize) / 2),
            int((insize - oldsize) / 2):int((insize + oldsize) / 2)]
    del F0
    return FF


def calculation_figure(ax, Q, sep, k, w0=2.5e-6, L=50e-6, res=1e-7, exact=True, normalize=False, return_field=False, find_zeroes=False, *args, **kw):
    x, y, r, theta = grid(L, res)

    if exact:
        E0 = vortex_beam(r, theta, Q, w0)
    else:
        E0 = vortex_beam_by_fourier(r, theta, Q, w0)

    Eout = N.zeros_like(E0)
    for ix in range(E0.shape[1]):
        Eout[:, ix] = diffract(E0[:, ix], y[:, ix], sep, k, res)

    intens = N.abs(Eout) ** 2
    if normalize:
        intens /= intens.max()

    hw = L * 5e5  # halfwidth of view
    p = ax.imshow(intens, extent=(-hw, hw, -hw, hw), *args, **kw)

    if find_zeroes:
        ys, xs = local_minima(intens)
        minima = zip(ys, xs)
        minima.sort(key=lambda c: N.sqrt(x[c] ** 2 + y[c] ** 2))
        ys, xs = tuple(zip(*minima[0:int(N.ceil(Q))]))
        ax.scatter(
            (N.array(xs) * res - L / 2) * 1e6,
            (N.array(ys) * res - L / 2) * 1e6,
            color='black', marker='o', s=3)

    if return_field:
        return intens, p
    return p


def measurement_figure(ax, datapath, sep, *args, **kw):
    MICRONS_PER_PIXEL = 50.0 / 332.0

    files = glob.glob(datapath + '/sep {0} d 100 dist *.dat'.format(sep))
    xs = list(set([float(re.search(r'dist ([0-9]{1,2}\.[0-9]{2})',
        os.path.basename(file)).group(1))
        for file in files]))
    xs.sort()

    slit = N.zeros((len(xs), 512))
    for idx, x in enumerate(xs):
        slit[idx, :] = N.loadtxt(
            datapath + '/sep {0} d 100 dist {1:.02f}.dat'.format(sep, x),
            delimiter='\t')

    p = ax.imshow(slit.T,
        extent=(min(xs), max(xs), 0, 512 * MICRONS_PER_PIXEL), *args, **kw)
    return p


def local_minima(arr):
    # http://stackoverflow.com/questions/3684484/peak-detection-in-a-2d-array/3689710#3689710
    """
    Takes an array and detects the troughs using the local maximum filter.
    Returns a boolean mask of the troughs (i.e. 1 when
    the pixel's value is the neighborhood maximum, 0 otherwise)
    """
    neighborhood = morphology.generate_binary_structure(len(arr.shape), 2)
    local_min = (filters.minimum_filter(arr, footprint=neighborhood) == arr)
    background = (arr == 0)
    eroded_background = morphology.binary_erosion(
        background, structure=neighborhood, border_value=1)
    detected_minima = local_min - eroded_background
    return N.where(detected_minima)
