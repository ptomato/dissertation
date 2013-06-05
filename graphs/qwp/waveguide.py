import numpy as N
from scipy.optimize import fsolve

# Snyder & Love, pp. 240-244


# Trick to get scipy to solve complex equations
# http://mail.scipy.org/pipermail/scipy-user/2006-November/009943.html
def pack_into_real(cy):
    '''Pack a complex array into a real array.'''
    # Too clever by half, but it works.
    return N.column_stack([cy.real, cy.imag]).ravel()


def unpack_into_complex(y):
    '''Unpack a complex array from a real array.'''
    return y[::2] + 1j * y[1::2]


# Eigenvalue equations
def ev_TE(beta_packed, epsilon, n2, b, wl):
    beta2 = unpack_into_complex(beta_packed) ** 2
    k02 = (2 * N.pi / wl) ** 2
    W1 = N.sqrt(beta2 - k02 * epsilon)
    U1 = N.sqrt(k02 * n2 ** 2 - beta2)
    return pack_into_real(W1 / U1 - N.tan(0.5 * b * U1))


def ev_TM(beta_packed, epsilon, n2, b, wl):
    beta2 = unpack_into_complex(beta_packed) ** 2
    k02 = (2 * N.pi / wl) ** 2
    n22 = n2 ** 2
    W1 = N.sqrt(beta2 - k02 * epsilon)
    U1 = N.sqrt(k02 * n22 - beta2)
    return pack_into_real(n22 * W1 / (epsilon * U1) - N.tan(0.5 * b * U1))


# Initial guesses for solver
def TE_guess(b, wl):
    """Initial TE guess"""
    ny_TE_guess = N.array((0.439 * wl) / b, dtype=complex)
    beta_TE_guess = 2 * N.pi * N.sqrt(1 - ny_TE_guess ** 2) / wl
    return beta_TE_guess


def TM_guess(b):
    """Initial TM guess"""
    ny_TM_guess = 8e6 + 1e5j * N.ones_like(b)
    return ny_TM_guess


def _solve_beta(b, epsilon, n2, wl, beta_TE_guess, beta_TM_guess, verbose=False):
    """Solve the eigenvalue equations numerically"""

    # Output arrays
    beta_TE = N.zeros(b.shape, dtype=complex)
    beta_TM = N.zeros_like(beta_TE)

    for ix, width in enumerate(b):
        if verbose:
            print ix,
            if ix % 10 == 9:
                print ' '

        # first TE
        beta_packed, _, ier, mesg = fsolve(ev_TE,
            pack_into_real(beta_TE_guess[ix]),
            args=(epsilon, n2, width, wl),
            full_output=True)
        if ier != 1:
            print "For width={0} nm, no TE solution found: {1}".format(width * 1e9, mesg)
            beta_TE[ix] = N.nan
        else:
            beta_TE[ix] = unpack_into_complex(beta_packed)[0]

        # then TM
        beta_packed, _, ier, mesg = fsolve(ev_TM,
            pack_into_real(beta_TM_guess[ix]),
            args=(epsilon, n2, width, wl),
            full_output=True)
        if ier != 1:
            print "For width={0} nm, no TM solution found: {1}".format(width * 1e9, mesg)
            beta_TM[ix] = N.nan
        else:
            beta_TM[ix] = unpack_into_complex(beta_packed)[0]

    return beta_TE, beta_TM


def effective_mode_indices(b, epsilon, n2, wl, filename='waveguide_eff_indices.txt', verbose=True):
    beta_TE_guess = TE_guess(b, wl)
    beta_TM_guess = TM_guess(b)

    beta_TE, beta_TM = _solve_beta(b, epsilon, n2, wl, beta_TE_guess, beta_TM_guess, verbose)

    if verbose:
        print ' '
    if filename is not None:
        N.savetxt(filename, N.column_stack([
            beta_TE.view(float).reshape(-1, 2),
            beta_TM.view(float).reshape(-1, 2)
        ]))

    return beta_TE, beta_TM

if __name__ == '__main__':
    import matplotlib.pyplot as P

    b = N.arange(10, 1000, 2) * 1e-9
    wl = 830e-9
    epsilon = -29.321 + 2.051j
    n2 = 1.0
    teguess = TE_guess(b, wl)
    tmguess = TM_guess(b)
    te, tm = _solve_beta(b, epsilon, n2, wl, teguess, tmguess)

    fig = P.figure()
    ax = fig.gca()
    ax.plot(b * 1e9, te.real, 'b-')
    ax.plot(b * 1e9, teguess.real, 'b--')
    ax.plot(b * 1e9, te.imag, 'r-')
    ax.plot(b * 1e9, teguess.imag, 'r--')
    ax.plot(b * 1e9, tm.real, 'k-')
    ax.plot(b * 1e9, tmguess.real, 'k--')
    ax.plot(b * 1e9, tm.imag, 'g-')
    ax.plot(b * 1e9, tmguess.imag, 'g--')
    ax.set_ylim(-1e7, 10e7)
    P.show()
