# Acoustic, psychoacoustic, and orchestration source registry

This is a developer/audit registry, not the public bibliography. Entries marked pending or PAGE_REQUIRED_DO_NOT_RELEASE are not release-ready scholarly citations and must not be cited as page-grounded evidence.

## Canonical machine-readable registry

Authoritative structured entries: **`src/homogeneity_analyser/acoustic_profiles/source_registry.json`** (JSON). A human pointer file **`source_registry.yaml`** may sit beside it for editor orientation.

## Rules of use

- **No PDFs** are committed under `docs/`, `src/`, or tests. Optional working copies belong only under `private_sources/` (gitignored) and must not be shipped.
- Registry text is **paraphrase-first**; any `short_quote_optional` field is capped by automated validation.
- The JSON field `pages_consulted` may contain a **non-release placeholder** until maintainers record verified pagination from a held copy. Markdown in this file reports that state as **pending page verification** instead of echoing the raw placeholder.

## Release governance

`source_validation.get_acoustic_model_governed_source_keys()` is currently **empty**. When a future acoustic or fusion configuration binds parameters to specific `source_key` values, those keys must ship with verified `pages_consulted` before release-governed numeric binds.

## Summary table

| `source_key` | Short reference | Pages (audit) | Evidence type | Reliability |
| --- | --- | --- | --- | --- |
| `analysis_musical_instrument_tones_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Analysis of Musical Instrument Tones (exact title per document)* | pending page verification | signal_analysis | low |
| `benade_1976_fundamentals_musical_acoustics` | Benade, Arthur H. (1976). *Fundamentals of Musical Acoustics* | pending page verification | musical_instrument_acoustics | high |
| `campbell_acoustics_musical_instruments_pending` | Campbell, M. (initials/affiliation unverified in registry) (n.d.). *Acoustics of Musical Instruments (exact title per document)* | pending page verification | musical_instrument_acoustics | low |
| `campbell_gilbert_myers_2021_science_of_brass_instruments` | Campbell, Murray; Gilbert, Joël; Myers, Arnold (2021). *The Science of Brass Instruments* | pending page verification | musical_instrument_acoustics | high |
| `clarinet_spectrum_theory_experiment_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *The clarinet spectrum: theory and experiment (punctuation per PDF)* | pending page verification | musical_instrument_acoustics | medium |
| `discrimination_musical_instrument_sounds_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Discrimination of musical instrument sounds (exact title per document)* | pending page verification | psychoacoustics | low |
| `fixed_average_spectra_orchestral_instrument_tones_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Fixed Average Spectra of Orchestral Instrument Tones* | pending page verification | measured_acoustic_data | medium |
| `fletcher_rossing_1998_physics_of_musical_instruments` | Fletcher, Neville H.; Rossing, Thomas D. (1998). *The Physics of Musical Instruments* | pending page verification | theoretical_acoustics | high |
| `homogeneity_analyser_timbral_fusion_evidence_stub` | Homogeneity Analyser project (2026). *Internal evidence map for symbolic timbral and planned fusion layers* | N/A (project documentation; no private PDF) | project_specific | medium |
| `index_relative_quality_musical_instruments_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Index for the Relative Quality among Musical Instruments* | pending page verification | instrument_classification | low |
| `meyer_acoustics_performance_of_music` | Meyer, Jürgen (2009). *Acoustics and the Performance of Music* | pending page verification | orchestration_performance_acoustics | medium |
| `musical_instrument_classification_higher_order_spectra_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Musical instrument classification using higher order spectra* | pending page verification | instrument_classification | medium |
| `musical_instrument_timbres_classification_spectral_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Musical Instrument Timbres Classification with Spectral Features* | pending page verification | instrument_classification | medium |
| `physical_correlates_brass_instrument_tones_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Physical Correlates of Brass-Instrument Tones* | pending page verification | musical_instrument_acoustics | low |
| `relevance_spectral_features_instrument_classification_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *On the relevance of spectral features for instrument classification* | pending page verification | spectral_features | medium |
| `rossing_2010_science_of_string_instruments` | Rossing, Thomas D. (editor); multiple contributors (2010). *The Science of String Instruments* | pending page verification | musical_instrument_acoustics | high |
| `rossing_et_al_science_of_sound_pearson` | Rossing, Thomas D.; Wheeler, Paul A.; Fahy, Frank (editions vary) (2014). *Science of Sound (Pearson international edition; title varies by printing)* | pending page verification | psychoacoustics | medium |
| `same_family_relief_rationale_sources` | Homogeneity Analyser project (registry grouping) (2026). *Bibliographic cluster for H_notated_fusion_potential same-family relief calibrat* | N/A (metadata group; consult individual source_key rows cited in docs/archive_legacy/model_audit/H_NOTATED_FUSION_POTENT | project_specific | medium |
| `science_percussion_instruments_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Science of Percussion Instruments* | pending page verification | musical_instrument_acoustics | medium |
| `sivian_dunn_white_1931_absolute_amplitudes_spectra` | Sivian, L. J.; Dunn, H. K.; White, S. D. (1931). *Absolute Amplitudes and Spectra of Certain Musical Instruments and Orchestras* | 330-371 (journal pagination; verify scan numbering before citing as PDF page numbers) | measured_acoustic_data | high |
| `sound_power_timbre_dynamic_strength_orchestral_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Sound power and timbre as cues for the dynamic strength of orchestral instrument* | pending page verification | orchestration_performance_acoustics | medium |
| `sound_production_double_reed_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Sound Production Analysis of a Double Reed Instrument* | pending page verification | musical_instrument_acoustics | low |
| `statistical_analysis_musical_instruments_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Statistical Analysis of Musical Instruments (exact title per document)* | pending page verification | signal_analysis | low |
| `statistical_study_spectral_parameters_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Statistical study of spectral parameters in musical instrument (full title per P* | pending page verification | spectral_features | low |
| `tonal_spectra_wind_instruments_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Tonal Spectra of Wind Instruments* | pending page verification | measured_acoustic_data | medium |
| `viola_tonnerre_pending` | *(redacted in public docs; see canonical JSON for maintainer notes)* (n.d.). *Viola Tonnerre (exact title per PDF)* | pending page verification | musical_instrument_acoustics | low |

## Per-key detail (from JSON; filenames omitted from GitHub docs)

### `analysis_musical_instrument_tones_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Analysis of Musical Instrument Tones (exact title per document)
- **Publication or book:** Article or chapter (venue pending curation)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** signal_analysis
- **Reliability:** low
- **Used for:** Instrument tone analysis / spectral envelope methods (literature trail).
- **Notes:** Year not verified. Curate DOI and pagination from the private scan.

### `benade_1976_fundamentals_musical_acoustics`

- **Authors:** Benade, Arthur H.
- **Year:** 1976
- **Title:** Fundamentals of Musical Acoustics
- **Publication or book:** Oxford University Press
- **Publisher:** Oxford University Press
- **Edition:** 1
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** musical_instrument_acoustics
- **Reliability:** high
- **Used for:** Woodwind air column modes, clarinet-like odd-harmonic behavior, brass lip reed basics.
- **Notes:** Paraphrase: canonical pedagogical reference for musical instrument acoustics. PDF page map not verified here.

### `campbell_acoustics_musical_instruments_pending`

- **Authors:** Campbell, M. (initials/affiliation unverified in registry)
- **Title:** Acoustics of Musical Instruments (exact title per document)
- **Publication or book:** Monograph or proceedings (verify imprint)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** musical_instrument_acoustics
- **Reliability:** low
- **Used for:** General instrument acoustics cross-checks for taxonomy and timbre proxies.
- **Notes:** Year not verified. Filename suggests Murray Campbell-related material; confirm bibliographic record.

### `campbell_gilbert_myers_2021_science_of_brass_instruments`

- **Authors:** Campbell, Murray; Gilbert, Joël; Myers, Arnold
- **Year:** 2021
- **Title:** The Science of Brass Instruments
- **Publication or book:** Springer Nature (Modern Acoustics and Signal Processing)
- **Publisher:** Springer
- **Edition:** 1
- **DOI or URL:** https://doi.org/10.1007/978-3-030-55686-0
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** musical_instrument_acoustics
- **Reliability:** high
- **Used for:** Brass bore, radiation, and timbre science for orchestration-informed heuristics.
- **Notes:** *(redacted in public docs; see canonical JSON for maintainer notes)*

### `clarinet_spectrum_theory_experiment_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** The clarinet spectrum: theory and experiment (punctuation per PDF)
- **Publication or book:** Peer-reviewed article (pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** musical_instrument_acoustics
- **Reliability:** medium
- **Used for:** Clarinet odd-harmonic / cutoff literature for clarinet pairwise heuristics.
- **Notes:** Year not verified.

### `discrimination_musical_instrument_sounds_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Discrimination of musical instrument sounds (exact title per document)
- **Publication or book:** Peer-reviewed article (venue pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** psychoacoustics
- **Reliability:** low
- **Used for:** Listening discrimination / similarity cues relevant to fusion weighting literature.
- **Notes:** Year not verified.

### `fixed_average_spectra_orchestral_instrument_tones_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Fixed Average Spectra of Orchestral Instrument Tones
- **Publication or book:** Peer-reviewed article (venue pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** measured_acoustic_data
- **Reliability:** medium
- **Used for:** Orchestral instrument long-term average spectra (context for static heuristic tables).
- **Notes:** Year not verified.

### `fletcher_rossing_1998_physics_of_musical_instruments`

- **Authors:** Fletcher, Neville H.; Rossing, Thomas D.
- **Year:** 1998
- **Title:** The Physics of Musical Instruments
- **Publication or book:** Springer-Verlag New York (2nd ed. commonly catalogued)
- **Publisher:** Springer
- **Edition:** 2
- **DOI or URL:** https://doi.org/10.1007/978-0-387-21603-4
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** theoretical_acoustics
- **Reliability:** high
- **Used for:** Resonator models, string/wind/brass principles for high-level acoustic proxies.
- **Notes:** Paraphrase: standard reference for linear and nonlinear oscillators in musical instruments. PDF page numbers not verified in this registry.

### `homogeneity_analyser_timbral_fusion_evidence_stub`

- **Authors:** Homogeneity Analyser project
- **Year:** 2026
- **Title:** Internal evidence map for symbolic timbral and planned fusion layers
- **Publication or book:** Project documentation (this repository)
- **Pages consulted (audit):** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Evidence type:** project_specific
- **Reliability:** medium
- **Used for:** Tracks which registry keys will bind to future acoustic_heuristic / fusion configuration.
- **Notes:** Paraphrase: placeholder entry satisfying project_specific evidence; not a peer-reviewed acoustic measurement.

### `index_relative_quality_musical_instruments_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Index for the Relative Quality among Musical Instruments
- **Publication or book:** Unknown venue (curate from document)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** instrument_classification
- **Reliability:** low
- **Used for:** Historical / qualitative ranking context (not used in formulas).
- **Notes:** Year not verified.

### `meyer_acoustics_performance_of_music`

- **Authors:** Meyer, Jürgen
- **Year:** 2009
- **Title:** Acoustics and the Performance of Music
- **Publication or book:** Book (English-language reference edition; verify imprint against held copy)
- **Publisher:** Springer / Focal (imprint varies by edition; verify)
- **Edition:** Verify against held copy
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** orchestration_performance_acoustics
- **Reliability:** medium
- **Used for:** Room-orchestra balance, dynamic strength, and performance acoustics context.
- **Notes:** Year/edition paraphrased from widely catalogued English editions; confirm exact imprint on private copy. Not used at runtime.

### `musical_instrument_classification_higher_order_spectra_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Musical instrument classification using higher order spectra
- **Publication or book:** Conference or journal (pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** instrument_classification
- **Reliability:** medium
- **Used for:** Higher-order spectral features for classification (literature trail).
- **Notes:** Year not verified.

### `musical_instrument_timbres_classification_spectral_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Musical Instrument Timbres Classification with Spectral Features
- **Publication or book:** Conference or journal (pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** instrument_classification
- **Reliability:** medium
- **Used for:** MFCC / spectral-feature classifiers as literature context for future acoustic_heuristic mode.
- **Notes:** Year not verified.

### `physical_correlates_brass_instrument_tones_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Physical Correlates of Brass-Instrument Tones
- **Publication or book:** Peer-reviewed article (venue to be confirmed from document)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** musical_instrument_acoustics
- **Reliability:** low
- **Used for:** Brass timbre / radiated spectrum correlates (planned acoustic-h proxy layer).
- **Notes:** Year not verified. Filename suggests brass tone correlates; do not cite page numbers until verified on the held copy.

### `relevance_spectral_features_instrument_classification_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** On the relevance of spectral features for instrument classification
- **Publication or book:** Conference or journal (pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** spectral_features
- **Reliability:** medium
- **Used for:** Feature relevance for classifier design (documentation only).
- **Notes:** Year not verified.

### `rossing_2010_science_of_string_instruments`

- **Authors:** Rossing, Thomas D. (editor); multiple contributors
- **Year:** 2010
- **Title:** The Science of String Instruments
- **Publication or book:** Springer Science+Business Media
- **Publisher:** Springer
- **Edition:** 1
- **DOI or URL:** https://doi.org/10.1007/978-1-4419-7110-4
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** musical_instrument_acoustics
- **Reliability:** high
- **Used for:** Bow-string spectra, body modes, and timbre for string-family heuristics.
- **Notes:** Paraphrase: edited survey of string-instrument acoustics. Confirm pagination on held scan before citing pages.

### `rossing_et_al_science_of_sound_pearson`

- **Authors:** Rossing, Thomas D.; Wheeler, Paul A.; Fahy, Frank (editions vary)
- **Year:** 2014
- **Title:** Science of Sound (Pearson international edition; title varies by printing)
- **Publication or book:** Pearson Education (international editions catalogued under similar titles)
- **Publisher:** Pearson
- **Edition:** Verify printing (e.g., 4th or New International Edition)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** psychoacoustics
- **Reliability:** medium
- **Used for:** Psychoacoustics fundamentals (loudness, pitch, timbre descriptors) for fusion documentation.
- **Notes:** *(redacted in public docs; see canonical JSON for maintainer notes)*

### `same_family_relief_rationale_sources`

- **Authors:** Homogeneity Analyser project (registry grouping)
- **Year:** 2026
- **Title:** Bibliographic cluster for H_notated_fusion_potential same-family relief calibration
- **Publication or book:** Synthetic registry grouping (this repository)
- **Pages consulted (audit):** N/A (metadata group; consult individual source_key rows cited in docs/archive_legacy/model_audit/H_NOTATED_FUSION_POTENTIAL_JUSTIFICATION.md)
- **Evidence type:** project_specific
- **Reliability:** medium
- **Used for:** Links default_profiles.json constant same_family_relief_balanced_default to literature-motivated rationale without claiming a single printed page proves the numeric value.
- **Notes:** *(Monograph rows in JSON may still use internal page placeholders until verified on a held copy; see the disclaimer at the top of this file.)*

### `science_percussion_instruments_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Science of Percussion Instruments
- **Publication or book:** Book or monograph (pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** musical_instrument_acoustics
- **Reliability:** medium
- **Used for:** Percussion timbre and bar/membrane modes for ontology notes.
- **Notes:** Year not verified.

### `sivian_dunn_white_1931_absolute_amplitudes_spectra`

- **Authors:** Sivian, L. J.; Dunn, H. K.; White, S. D.
- **Year:** 1931
- **Title:** Absolute Amplitudes and Spectra of Certain Musical Instruments and Orchestras
- **Publication or book:** The Journal of the Acoustical Society of America
- **Publisher:** Acoustical Society of America (AIP Publishing)
- **Volume:** 2
- **Issue:** 3
- **Article pages (metadata):** 330-371
- **DOI or URL:** https://doi.org/10.1121/1.1915260
- **Pages consulted (audit):** 330-371 (journal pagination; verify scan numbering before citing as PDF page numbers)
- **Evidence type:** measured_acoustic_data
- **Reliability:** high
- **Used for:** Early orchestral and instrument absolute spectra / levels; contextualizes fixed spectral heuristics.
- **Notes:** Paraphrase: foundational measured spectra and amplitudes for several instruments and orchestral passages. Use for literature context for orchestral spectra, not as a substitute for audio analysis in this codebase.

### `sound_power_timbre_dynamic_strength_orchestral_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Sound power and timbre as cues for the dynamic strength of orchestral instruments
- **Publication or book:** Peer-reviewed article (venue pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** orchestration_performance_acoustics
- **Reliability:** medium
- **Used for:** Linking timbral cues to perceived dynamic strength in orchestral texture.
- **Notes:** Year not verified.

### `sound_production_double_reed_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Sound Production Analysis of a Double Reed Instrument
- **Publication or book:** Thesis or article (pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** musical_instrument_acoustics
- **Reliability:** low
- **Used for:** Double-reed excitation and spectrum context.
- **Notes:** Year not verified.

### `statistical_analysis_musical_instruments_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Statistical Analysis of Musical Instruments (exact title per document)
- **Publication or book:** Article or report (venue pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** signal_analysis
- **Reliability:** low
- **Used for:** Statistical spectral models for instrument families.
- **Notes:** Year not verified.

### `statistical_study_spectral_parameters_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Statistical study of spectral parameters in musical instrument (full title per PDF)
- **Publication or book:** Peer-reviewed article (pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** spectral_features
- **Reliability:** low
- **Used for:** Distributions of spectral parameters across instruments.
- **Notes:** Year not verified.

### `tonal_spectra_wind_instruments_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Tonal Spectra of Wind Instruments
- **Publication or book:** Peer-reviewed article (pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** measured_acoustic_data
- **Reliability:** medium
- **Used for:** Wind-instrument steady-state spectra references.
- **Notes:** Year not verified.

### `viola_tonnerre_pending`

- **Authors:** *(redacted in public docs; see canonical JSON for maintainer notes)*
- **Title:** Viola Tonnerre (exact title per PDF)
- **Publication or book:** Unknown venue (likely French-language; pending)
- **Pages consulted (audit):** *(pending page verification — record real pagination from a held copy before citing)*
- **Evidence type:** musical_instrument_acoustics
- **Reliability:** low
- **Used for:** Viola-specific acoustics or repertoire context if curated.
- **Notes:** Year not verified.

## Maintenance

1. Curate missing years, venues, and DOIs from **held copies** (do not commit PDFs).
2. Replace pending `pages_consulted` placeholders in JSON with verified page spans once confirmed.
3. When bulk-editing structured entries, use **`scripts/build_acoustic_source_registry_json.py`** if applicable, then run **`pytest tests/test_acoustic_source_registry.py`**.
