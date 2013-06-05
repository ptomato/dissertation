# Definitions
PYTHON=python -u
INKSCAPE=inkscape --without-gui
RM=rm -f
XELATEX=xelatex --interaction=nonstopmode --synctex=1 --enable-write18 --max-print-line=120
TEXLOG=texloganalyser.py -beiw
BIBER=biber
# BIBER=./biber.exe

.PHONY: all clean
.SUFFIXES: .svg .pdf
.PRECIOUS: %.bbl
.DELETE_ON_ERROR: main.pdf

.svg.pdf:
	$(INKSCAPE) --export-latex --export-area-page --export-pdf=$@ $<

# Top-level targets

all: stellingen.pdf stellingen-nl.pdf main.pdf
# all: main.pdf

clean:
	-$(RM) *.aux
	-$(RM) chapters/*.aux
	-$(RM) main.acn main.bbl main.bcf main.blg main.glo main.ist main.log main.out main.pdf main.run.xml main.synctex* main.toc
	-$(RM) graphs/*.pyc
	-$(RM) graphs/qwp/*.pyc graphs/qwp/waveguide_eff_indices_*.txt
	-$(RM) bibliography/*.pyc

# Bibliography

bibliography/library.bib: bibliography/library-full.rdf
	$(PYTHON) bibliography/zotero2bibtex.py --biber --acronyms $< $@

# Graphs

graphs/%.pdf:
	cd $(@D) && $(PYTHON) ../../$< batch

PLOT_DEPS = graphs/plot_config.py graphs/tango.py
QWP_DEPS = graphs/qwp/simulation.py graphs/qwp/spp_generation.py graphs/qwp/waveguide.py

graphs/introduction/aluminum-dip.pdf: graphs/introduction/figure-reflection-dip.py $(PLOT_DEPS)
# graphs/introduction/bulk-aluminum-sp-dispersion.pdf: graphs/introduction/figure-infinite-sp-dispersion.py $(PLOT_DEPS)

graphs/qwp/birefringence.pdf graphs/qwp/dichroism.pdf: graphs/qwp/figure-results.py $(PLOT_DEPS) $(QWP_DEPS)
graphs/qwp/coupling.pdf: graphs/qwp/figure-coupling.py $(PLOT_DEPS) $(QWP_DEPS)
graphs/qwp/stokes-parameters.pdf: graphs/qwp/figure-stokes-parameters.py $(PLOT_DEPS) $(QWP_DEPS)
graphs/qwp/poincare.png: graphs/qwp/figure-poincare.py $(QWP_DEPS)
	cd $(@D) && $(PYTHON) ../../$< batch
graphs/qwp/scattering-profile.pdf: graphs/qwp/figure-scattering-profile.py $(PLOT_DEPS) $(QWP_DEPS)
graphs/qwp/correction-factors.pdf: graphs/qwp/figure-correction.py $(QWP_DEPS) $(PLOT_DEPS)

graphs/soc/expected-near-field.pdf: graphs/soc/figure-expected-nf.py $(PLOT_DEPS)
graphs/soc/measured-near-field.pdf graphs/soc/stokes-analysis.pdf: graphs/soc/figure-measured-nf.py $(PLOT_DEPS)
graphs/soc/groove-near-field.pdf graphs/soc/groove-stokes-analysis.pdf: graphs/soc/figure-groove-nf.py $(PLOT_DEPS)
graphs/soc/far-field-measurements.pdf: graphs/soc/figure-farfield.py $(PLOT_DEPS)

TOMOGRAPHY_DEPS = graphs/tomography/diffraction.py graphs/epsilons.py

graphs/tomography/charge.pdf graphs/tomography/distance.pdf: graphs/tomography/figure-charge-tomograms.py $(PLOT_DEPS) $(TOMOGRAPHY_DEPS)
graphs/tomography/diffraction.pdf: graphs/tomography/figure-diffraction.py $(PLOT_DEPS) $(TOMOGRAPHY_DEPS)
graphs/tomography/halfvortex.pdf: graphs/tomography/figure-halfvortex.py $(PLOT_DEPS) $(TOMOGRAPHY_DEPS)
graphs/tomography/charge-evolution.pdf: graphs/tomography/figure-charge-evolution.py $(PLOT_DEPS) $(TOMOGRAPHY_DEPS)

DRUDIUM_DEPS = graphs/layer_calculations.py graphs/drudium/drudium.py
MATRIX_METHOD_DEPS = graphs/matrix_method.py graphs/local_extrema.py

graphs/drudium/optical-properties.pdf graphs/drudium/plasmonic-properties.pdf: graphs/drudium/figure-drudium.py graphs/drudium/drudium.py $(PLOT_DEPS)
graphs/drudium/typical-spr.pdf graphs/drudium/wavelength-spr.pdf graphs/drudium/wavelength-spr-exptl.pdf: graphs/drudium/figure-spr-curves.py $(PLOT_DEPS) $(DRUDIUM_DEPS)
graphs/drudium/critical-coupling.pdf graphs/drudium/critical-coupling-otto.pdf: graphs/drudium/figure-optimum-thickness.py $(PLOT_DEPS) $(DRUDIUM_DEPS)
graphs/drudium/wavelength-otto.pdf graphs/drudium/wavelength-otto-exptl.pdf: graphs/drudium/figure-otto-curves.py $(PLOT_DEPS) $(DRUDIUM_DEPS)
graphs/drudium/comparison.pdf graphs/drudium/otto-comparison.pdf graphs/drudium/realistic-comparison.pdf: graphs/drudium/figure-reflection-fitting.py $(PLOT_DEPS) $(DRUDIUM_DEPS) graphs/epsilons.py $(MATRIX_METHOD_DEPS)

PRISM_DATA = \
	data/kretschmann/ALP4RT.txt \
	data/kretschmann/OP1RT.txt \
	data/kretschmann/OP1LT.txt
$(PRISM_DATA): data/kretschmann/analyze-data.py data/kretschmann/_INDEX.json graphs/epsilons.py graphs/layer_calculations.py data/kretschmann/curve_fit_fixed_params.py
	cd $(@D) && $(PYTHON) analyze-data.py

ASHCROFT_DEPS = graphs/ashcroft.py graphs/crystal_plane.py

graphs/kretschmann/kretschmann-layers.pdf graphs/kretschmann/otto-layers.pdf: graphs/kretschmann/figure-mode.py $(PLOT_DEPS) $(MATRIX_METHOD_DEPS) graphs/epsilons.py
graphs/kretschmann/kretschmann-curves.pdf graphs/kretschmann/otto-curves.pdf: graphs/kretschmann/figure-measured-curves.py $(PLOT_DEPS) graphs/epsilons.py data/kretschmann/ALP4RT.txt data/kretschmann/OP1RT.txt
graphs/kretschmann/minimum-reflectance.pdf: graphs/kretschmann/figure-resonance-minima.py $(PLOT_DEPS) data/kretschmann/ALP4RT.txt data/kretschmann/OP1RT.txt
graphs/kretschmann/mode-index.pdf: graphs/kretschmann/figure-mode-index.py $(PLOT_DEPS) $(MATRIX_METHOD_DEPS) $(ASHCROFT_DEPS) data/kretschmann/ALP4RT.txt data/kretschmann/OP1RT.txt
graphs/kretschmann/eps1.pdf: graphs/kretschmann/figure-fit-eps1.py $(PLOT_DEPS) $(ASHCROFT_DEPS) graphs/kretschmann/read_wvase_file.py data/kretschmann/ALP4RT.txt

graphs/otto/temperature-dependence.pdf: graphs/otto/figure-ashcroft.py $(PLOT_DEPS) $(ASHCROFT_DEPS)
graphs/otto/measured-curves.pdf: graphs/otto/figure-measured-curves.py $(PLOT_DEPS) graphs/epsilons.py data/kretschmann/OP1LT.txt
graphs/otto/minimum-reflectance.pdf: graphs/otto/figure-resonance-minima.py $(PLOT_DEPS) data/kretschmann/OP1LT.txt data/kretschmann/OP1RT.txt
graphs/otto/mode-index.pdf: graphs/otto/figure-mode-index.py $(PLOT_DEPS) $(MATRIX_METHOD_DEPS) $(ASHCROFT_DEPS) graphs/epsilons.py data/kretschmann/OP1LT.txt
graphs/otto/group-index.pdf graphs/otto/dispersion.pdf: graphs/otto/figure-dispersion.py $(PLOT_DEPS) graphs/otto/savitzky_golay.py data/kretschmann/OP1LT.txt data/kretschmann/OP1RT.txt

GRAPHS= \
	graphs/introduction/aluminum-dip.pdf \
	graphs/qwp/birefringence.pdf \
	graphs/qwp/dichroism.pdf \
	graphs/qwp/coupling.pdf \
	graphs/qwp/stokes-parameters.pdf \
	graphs/qwp/scattering-profile.pdf \
	graphs/qwp/correction-factors.pdf \
	graphs/soc/expected-near-field.pdf \
	graphs/soc/measured-near-field.pdf \
	graphs/soc/stokes-analysis.pdf \
	graphs/soc/groove-near-field.pdf \
	graphs/soc/groove-stokes-analysis.pdf \
	graphs/soc/far-field-measurements.pdf \
	graphs/tomography/charge.pdf \
	graphs/tomography/distance.pdf \
	graphs/tomography/diffraction.pdf \
	graphs/tomography/halfvortex.pdf \
	graphs/tomography/charge-evolution.pdf \
	graphs/drudium/optical-properties.pdf \
	graphs/drudium/plasmonic-properties.pdf \
	graphs/drudium/typical-spr.pdf \
	graphs/drudium/critical-coupling.pdf \
	graphs/drudium/wavelength-spr.pdf \
	graphs/drudium/comparison.pdf \
	graphs/drudium/realistic-comparison.pdf \
	graphs/drudium/critical-coupling-otto.pdf \
	graphs/drudium/wavelength-otto.pdf \
	graphs/drudium/otto-comparison.pdf \
	graphs/drudium/wavelength-spr-exptl.pdf \
	graphs/drudium/wavelength-otto-exptl.pdf \
	graphs/kretschmann/kretschmann-layers.pdf \
	graphs/kretschmann/kretschmann-curves.pdf \
	graphs/kretschmann/otto-layers.pdf \
	graphs/kretschmann/otto-curves.pdf \
	graphs/kretschmann/minimum-reflectance.pdf \
	graphs/kretschmann/mode-index.pdf \
	graphs/kretschmann/eps1.pdf \
	graphs/otto/temperature-dependence.pdf \
	graphs/otto/measured-curves.pdf \
	graphs/otto/minimum-reflectance.pdf \
	graphs/otto/mode-index.pdf \
	graphs/otto/group-index.pdf \
	graphs/otto/dispersion.pdf

# Illustrations

ILLUSTRATIONS= \
	illustrations/introduction/jump-rope.pdf \
	illustrations/introduction/tidal-patterns.pdf \
	illustrations/qwp/Setup.pdf \
	illustrations/qwp/sample.pdf \
	illustrations/qwp/poincare.pdf \
	illustrations/qwp/geometry.pdf \
	illustrations/soc/ringslit.pdf \
	illustrations/soc/setup-nearfield.pdf \
	illustrations/soc/setup.pdf \
	illustrations/soc/grooveslit.pdf \
	illustrations/soc/plasmondiffraction.pdf \
	illustrations/tomography/fork-hologram.png \
	illustrations/tomography/sample.pdf \
	illustrations/tomography/setup.pdf \
	illustrations/tomography/single-slit-oblique.pdf \
	illustrations/tomography/double-slit-inphase.pdf \
	illustrations/tomography/double-slit-antiphase.pdf \
	illustrations/tomography/double-slit-cartoon.pdf \
	illustrations/tomography/spp.png \
	illustrations/drudium/infinite-interface.pdf \
	illustrations/drudium/configurations.pdf \
	illustrations/kretschmann/setup.pdf \
	illustrations/otto/otto-configuration.pdf

illustrations/qwp/sample.pdf: illustrations/qwp/staircase-slit.png
illustrations/qwp/geometry.pdf: illustrations/qwp/geometry.png
illustrations/qwp/poincare.pdf: graphs/qwp/poincare.png

# Chapters

CHAPTERS = \
	frontmatter.tex \
	chapters/introduction.tex \
	chapters/qwp.tex chapters/qwp-appendix.tex \
	chapters/soc.tex chapters/soc-appendix.tex \
	chapters/tomography.tex \
	chapters/drudium.tex chapters/drudium-appendix.tex \
	chapters/kretschmann.tex chapters/kretschmann-appendix.tex \
	chapters/otto.tex chapters/otto-appendix.tex \
	backmatter.tex

# Main

main.bbl: bibliography/library.bib
	$(XELATEX) main.tex | $(PYTHON) $(TEXLOG) && $(BIBER) main

# Set up for rerunning again if LaTeX says to rerun
# We have to change main.pdf's timestamp to 1980 instead of simply touch-ing
# main.tex, because the timestamp has 1 s resolution?!
main.pdf: main.tex main.bbl
	@$(XELATEX) $< | $(PYTHON) $(TEXLOG) && \
	if test ! -z "`grep 'Please (re)run Biber' $*.log`"; then \
		$(BIBER) $*; \
	fi; \
	if test ! -z "`grep -i rerun $*.log | grep -v rerunfilecheck`"; then \
		touch -t 198001010000 $@ ; \
		echo "Rerun notice detected. Type 'make' again to rerun."; \
	fi

main.pdf: bib-inc.tex fonts-inc.tex tufte-book-local.tex \
	$(CHAPTERS) $(GRAPHS) $(ILLUSTRATIONS)

stellingen.pdf: stellingen.tex stellingen.cls fonts-inc.tex
	@$(XELATEX) $< | $(PYTHON) $(TEXLOG) && \
	if test ! -z "`grep -i rerun $*.log | grep -v rerunfilecheck`"; then \
		touch -t 198001010000 $@ ; \
		echo "Rerun notice detected. Type 'make' again to rerun."; \
	fi
stellingen-nl.pdf: stellingen-nl.tex stellingen.cls fonts-inc.tex
	@$(XELATEX) $< | $(PYTHON) $(TEXLOG) && \
	if test ! -z "`grep -i rerun $*.log | grep -v rerunfilecheck`"; then \
		touch -t 198001010000 $@ ; \
		echo "Rerun notice detected. Type 'make' again to rerun."; \
	fi
