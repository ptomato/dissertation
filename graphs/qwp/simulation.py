import warnings
import numpy as N
import numpy.fft as FT
from scipy import integrate
from spp_generation import interface_calculation


class SlitSystem:
    """Simulation of a subwavelength slit in metal"""
    def __init__(self, slit_widths, wavelength, metal_epsilon, metal_thickness,
        incidence_index, slit_index, outcoupling_index, collection_index,
        numerical_aperture, angle_of_incidence,
        C1=1.0, C2=1.0, C3=1.0, caching=True):
        """
        Do the calculations for the subwavelength slit system.

        @slit_widths: An array of slit widths, in meters.
        @wavelength: Wavelength of the incident light, in meters.
        @metal_epsilon: Dielectric constant of the metal film.
        @metal_thickness: Thickness of the metal film, in meters.
        @incidence_index: Index of refraction of the medium from which the light
        is incident.
        @slit_index: Index of refraction of the medium inside the slit.
        @outcoupling_index: Index of refraction of the medium on the other side
        of the slit.
        @collection_index: Index of refraction of the medium in which the
        collection lens is situated.
        @numerical_aperture: numerical aperture of the collection lens.
        @angle_of_incidence: Angle under which the plane wave is incident on the
        slit.
        @C1, @C2, @C3: fitting parameter.
        @caching: whether to try to read the waveguide calculation from a file,
        and write it out if it is not there.
        """
        # Shorthand for parameters
        b = slit_widths
        wl = wavelength
        eps = metal_epsilon
        z = metal_thickness
        n1 = incidence_index
        n2 = slit_index
        n3 = outcoupling_index
        n4 = collection_index
        NA = numerical_aperture
        theta = angle_of_incidence

        k0 = 2 * N.pi / wl

        # P. Lalanne, J. P. Hugonin, J. C. Rodier. (2006). "Approximate model
        # for surface-plasmon generation at slit apertures." JOSA A 23 (7),
        # p. 1608.
        #
        # Model is valid for b <= wl, approximately.
        if N.any(b > wl):
            warnings.warn('Model is not valid for slit widths larger than the '
                + 'wavelength.')

        # eps_Ti = -5.649 + 25.787j  # Johnson & Christy
        _, _, alpha12, beta12 = interface_calculation(b, wl, eps, n1, n2, theta)
        _, _, alpha23, _ = interface_calculation(b, wl, eps, n3, n2, theta)

        # Snyder & Love, pp. 240-244.

        # Propagation constants of fundamental slit waveguide mode
        if caching:
            cache_filename = 'waveguide_eff_indices_{0}_{1}.txt'.format(int(wl * 1e9), b.size)
            try:
                beta_TE, beta_TM = N.loadtxt(cache_filename, unpack=True).view(complex)
            except IOError:
                from waveguide import effective_mode_indices
                beta_TE, beta_TM = effective_mode_indices(b, eps, n2, wl,
                    filename=cache_filename)
        else:
            from waveguide import effective_mode_indices
            beta_TE, beta_TM = effective_mode_indices(b, eps, n2, wl, filename=None)

        # Calculate collection efficiency of the optics.
        # First we calculate the mode profile at the exit of the slit, in a
        # one-dimensional half-space. (The modes are symmetric.)
        num = 2048
        num_padded = 32768
        lim = b.max() * 4
        space = N.linspace(0, lim, num=num).reshape(num, 1)

        # Extend the space for each slit width
        x = space.repeat(b.size, 1)

        # Mask for space inside the slit
        slit = x < b / 2

        # Electric field at end of slit
        root_TE = N.sqrt(k0 ** 2 * n2 ** 2 - beta_TE ** 2)
        root_TM = N.sqrt(k0 ** 2 * n2 ** 2 - beta_TM ** 2)
        root2_TE = N.sqrt(beta_TE ** 2 - k0 ** 2 * eps)
        root2_TM = N.sqrt(beta_TM ** 2 - k0 ** 2 * eps)

        Ey_TE_metal = N.exp(-(N.abs(x) - b / 2) * root2_TE)
        Ey_TE_metal[slit] = 0.0
        Ey_TE_slit = N.cos(x * root_TE) / N.cos(b * root_TE / 2)
        Ey_TE_slit[~slit] = 0.0
        Ey_TE = (Ey_TE_metal + Ey_TE_slit) * N.exp(1j * beta_TE * z)

        Ex_TM_metal = (n2 ** 2 / eps) * N.exp(-(N.abs(x) - b / 2) * root2_TM)
        Ex_TM_metal[slit] = 0.0
        Ex_TM_slit = N.cos(x * root_TM) / N.cos(b * root_TM / 2)
        Ex_TM_slit[~slit] = 0.0
        Ex_TM = (Ex_TM_metal + Ex_TM_slit) * N.exp(1j * beta_TM * z)

        self.field_Ey_TE = N.r_[Ey_TE[::-1], Ey_TE]
        self.field_Ex_TM = N.r_[Ex_TM[::-1], Ex_TM]
        self.field_x = N.r_[-x[::-1], x]

        # Fourier transform of electric field
        self.Fy_TE = FT.fft(Ey_TE, n=num_padded, axis=0)[:num] / num
        self.Fx_TM = FT.fft(Ex_TM, n=num_padded, axis=0)[:num] / num

        # Convert from spatial frequencies to angles
        spatial_frequencies = FT.fftfreq(num_padded, d=lim / num)[:num]
        max_spatial_frequency = spatial_frequencies[spatial_frequencies < (n3 / wl)].argmax() + 1
        # spatial_frequencies is in cycles / unit, so no extra factor of 2pi
        angles = N.append(N.arcsin(wl * spatial_frequencies[:max_spatial_frequency - 1] / n3), [N.pi / 2])
        self.spatial_frequencies = spatial_frequencies

        self.Fy_TE2 = N.abs(self.Fy_TE[:max_spatial_frequency, :]) ** 2
        self.Fx_TM2 = N.abs(self.Fx_TM[:max_spatial_frequency, :]) ** 2
        self.angles = angles

        # Calculate Fresnel reflection coefficient at n3-n4 interface
        if n3 == n4:
            self.R_TE, self.R_TM = N.zeros_like(angles), N.zeros_like(angles)
        else:
            critical_angle = N.arcsin(n4 / n3)
            mask = angles < critical_angle
            # For numerical computation considerations, we set R=1 above the
            # critical angle; this
            term1, term2 = N.ones_like(angles), N.zeros_like(angles)
            term1[mask] = n3 * N.cos(angles[mask])
            term2[mask] = n4 * N.sqrt(1 - ((n3 / n4) * N.sin(angles[mask])) ** 2)
            self.R_TE = ((term1 - term2) / (term1 + term2)) ** 2

            term1, term2 = N.ones_like(angles), N.zeros_like(angles)
            term1[mask] = n3 * N.sqrt(1 - ((n3 / n4) * N.sin(angles[mask])) ** 2)
            term2[mask] = n4 * N.cos(angles[mask])
            self.R_TM = ((term1 - term2) / (term1 + term2)) ** 2

        # This is what the objective sees
        self.profile_TE = (1 - self.R_TE)[:, N.newaxis] * self.Fy_TE2
        self.profile_TM = (1 - self.R_TM)[:, N.newaxis] * self.Fx_TM2

        # Integrate the intensity picked up by the objective normalized by the
        # total intensity
        max_collection_angle = N.arcsin(NA / n3)
        NA_cutoff = angles < max_collection_angle
        self.collection_eff_TE = \
            integrate.trapz(self.profile_TE[NA_cutoff], angles[NA_cutoff], axis=0) \
            / integrate.trapz(self.Fy_TE2, angles, axis=0)
        self.collection_eff_TM = \
            integrate.trapz(self.profile_TM[NA_cutoff], angles[NA_cutoff], axis=0) \
            / integrate.trapz(self.Fx_TM2, angles, axis=0)

        # Fresnel reflection and transmission coefficients to and from the slit
        # mode
        self.r21_TM = (k0 * n1 - beta_TM) / (k0 * n1 + beta_TM)
        t12_TM = (k0 * n1 / beta_TM) * (1 - self.r21_TM)
        self.r23_TM = (k0 * n3 - beta_TM) / (k0 * n3 + beta_TM)
        t23_TM = (beta_TM / (k0 * n3)) * (1 + self.r23_TM)
        r21_TE = (beta_TE - k0 * n1) / (beta_TE + k0 * n1)
        t12_TE = 1 - r21_TE
        r23_TE = (beta_TE - k0 * n3) / (beta_TE + k0 * n3)
        t23_TE = 1 + r23_TE

        # Fabry-Perot transmission coefficients
        self.t123_TM = t12_TM * t23_TM * N.exp(1j * beta_TM * z) \
            / (1 - self.r23_TM * self.r21_TM * N.exp(2j * beta_TM * z))
        self.t123_TE = t12_TE * t23_TE * N.exp(1j * beta_TE * z) \
            / (1 - r23_TE * r21_TE * N.exp(2j * beta_TE * z))

        # Surface plasmon generation coefficients
        self.s12 = beta12 + (t12_TM * self.r23_TM * alpha12
            * N.exp(2j * beta_TM * z)
            / (1 - self.r23_TM * self.r21_TM * N.exp(2j * beta_TM * z)))
        self.s23 = (t12_TM * alpha23 * N.exp(1j * beta_TM * z)
            / (1 - self.r23_TM * self.r21_TM * N.exp(2j * beta_TM * z)))

        # Total transmission (taking into account loss to surface plasmons on
        # both sides)
        self.T_TM = C1 * self.collection_eff_TM * (
            (n3 / n1) * N.abs(self.t123_TM) ** 2
            - 2 * N.abs(self.s12) ** 2
            - 2 * C2 * N.abs(self.s23) ** 2)
        self.T_TE = self.collection_eff_TE * (n3 / n1) ** 2 * N.abs(self.t123_TE) ** 2

        # Phase lag between TM and TE modes
        self.dphase = (N.angle(self.t123_TM) - N.angle(self.t123_TE)) \
            % (2 * N.pi)

        # Output results as object members
        self.beta_TE, self.beta_TM = beta_TE, beta_TM

if __name__ == '__main__':
    b = N.arange(10, 830, 2) * 1e-9
    b2 = N.arange(10, 830, 2) * 1e-9
    calc = SlitSystem(b,
        wavelength=830e-9,
        metal_epsilon=-29.321 + 2.051j,
        metal_thickness=200e-9,
        incidence_index=1.00027487,
        slit_index=1.00027487,
        outcoupling_index=1.5102,
        collection_index=1.00027487,
        numerical_aperture=0.40,
        angle_of_incidence=0.0)
    calc2 = SlitSystem(b2,
        wavelength=830e-9,
        metal_epsilon=-29.321 + 2.051j,
        metal_thickness=200e-9,
        incidence_index=1.5102,
        slit_index=1.00027487,
        outcoupling_index=1.00027487,
        collection_index=1.00027487,
        numerical_aperture=0.40,
        angle_of_incidence=0.0)

    from matplotlib import pyplot as P
    fig = P.figure()
    ax = fig.gca()
    ax.plot(b * 1e9, calc.collection_eff_TM, label='forward TM')
    ax.plot(b * 1e9, calc.collection_eff_TE, label='forward TE')
    ax.plot(b2 * 1e9, calc2.collection_eff_TM, label='reverse TM')
    ax.plot(b2 * 1e9, calc2.collection_eff_TE, label='reverse TE')
    ax.set_xlabel('Slit width (nm)')
    ax.set_ylabel('Fraction of total radiated energy collected by objective')
    ax.legend(loc='best')
    ax.set_xlim(0, 500)
    P.show()
