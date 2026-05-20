"""Static UI copy (keeps gradio_app layout readable)."""

INTRO_MARKDOWN = (
    "*Upload a score, set the window and optional weights, then click **Run analysis**. "
    "Expand **Symbolic inspection** for instrument inventory and event-level notation audit tables.*"
)

METRICS_EXPLAINER = (
    "**H_TI_core** is the **structural** curve: overlap-mass **Herfindahl** on canonical **instrument**, "
    "instrumental **subfamily** (`family` rows), **`technique_uniformity_key`**, plus **register compactness** "
    "(span + pairwise semitone proximity on sounding MIDI; not interval-class consonance) — "
    "combined as a **weighted geometric mean** (missing layers omitted; weights renormalised). "
    "**Written dynamics** feed the **notated dynamic conditioning** layer (ordinal evidence, not SPL); "
    "they **do not** rescale **H_TI_core**. "
    "Optional accordions add **interval-class / symbolic blend-potential** "
    "(stable keys e.g. **seconds_sevenths** = mod‑12 buckets, not literal interval names; "
    "see **literal_interval_semitone_pair_mass** for absolute semitone distances) or **H_TA_acoustic_proxy** "
    "(separate layers; default off). "
    "Exports also list **`H_TI`** with the **same numbers** as **H_TI_core**. "
    "**Not** measured audio, **not** waveform or FFT analysis, **not** measured acoustic or perceptual fusion."
)
