# Timbral score representation (sounding pitch, notation context, percussion register)

> **Legacy / internal documentation** — supports the **symbolic event pipeline** shared with **H_TI_core** (`SymbolicScoreAnalyzer`). Not a separate current user-facing metric tab.

**Terminology (H_TIMBRAL vs H_TI 3.0):** In this legacy/internal H_TIMBRAL document, terms such as “blend” refer to symbolic timbral-design or affinity heuristics within that module. They should not be confused with the H_TI 3.0 export fields. In H_TI 3.0, `H_TI_core` denotes score-based symbolic timbral–instrumental homogeneity; `register_compactness` denotes pitch-space proximity/dispersion; `interval_class_blend_factor` denotes symbolic interval-relation favourability; and `symbolic_blend_potential` is an optional interpretive diagnostic, not measured acoustic or perceptual fusion.

This note documents **notation-level** choices for ``H_timbral`` only. It does not change
how ``H(t)``, register uniformity ``U(t)``, or other analyzers read pitch.

## Sounding (concert) pitch for timbral tessitura

**Implementation:** ``homogeneity_analyser.analyzers.timbral_sounding_pitch.sounding_pitch_ps_list``

When ``TimbralHomogeneityAnalyzer`` builds per-note events, each pitch list is transposed
using ``note.getInstrument()`` when music21 exposes a typed instrument at that site
(including mid-part doublings such as flute → piccolo); otherwise the part default
``Instrument.transposition`` (Bb clarinet, F horn, Eb alto sax, etc.).

**Rationale:** timbral pairwise models (brass, woodwinds, sax, clarinet, …) interpret
MIDI pitch as a tessitura proxy. Using written pitch on transposing staves would skew
those comparisons.

**Scope:** applied on the shared symbolic event path (`symbolic_event_pipeline.py` / `symbolic_pitch_resolve.py`).
``parse_score`` / ``io/score_loader`` still returns the unmodified music21 score object.

## Technique text: note-local + same-measure directions

**Implementation:** ``homogeneity_analyser.analyzers.notation_context.notation_text_context_for_note``

By default (``measure_text="prior"``), measure-level ``TextExpression`` / ``RehearsalMark`` /
``Dynamic`` text is included only from **strictly earlier offsets** within the same
``Measure`` as the note, so a later marking does not apply retroactively to an earlier note.
``measure_text="legacy"`` restores the old “whole measure” merge (for explicit checks only).
``H_timbral`` event building uses ``measure_text="none"`` here and relies on chronological
``iter_timbral_elements`` + ``apply_persistent_text`` for persistent directions.

**Persistence rule:** only **direction** elements from ``iter_timbral_elements`` (staff
``TextExpression`` / rehearsal marks / dynamics in score order) update the per-part timeline
that carries ``pizz.`` → ``arco``, ``sul pont.`` → ``ord.``, etc. Note-local blobs from this
function are merged into a **copy** of that timeline for the current note’s
``merge_note_technique_state`` only; they **must not** advance the timeline for following
notes (so e.g. an expression attached only to note *n* does not impose ``sul tasto`` on note
*n+1*).

**Limitations:** no part-level or multi-measure lookahead; no arbitrary HTML; conservative
regex keywording unchanged in spirit. Unknown remains common when scores omit text.

## Percussion and the top-level register component

**Problem:** unpitched percussion often carries staff-line MIDI positions; ``ptp(pitches)``
across a window is not a musically meaningful “register” span.

**Mitigation:**

1. ``register_span_pitches`` in timbral features **omits** notes whose canonical percussion
   ontology marks ``pitch_status == unpitched``.
2. If the window is **percussion-dominated** and **unpitched-dominated**, the legacy
   register term is blended toward ``unpitched_percussion_register_proxy`` in
   ``percussion_pairwise_timbral`` (size-bin spread across unpitched hits).

Pitched / quasi-pitched percussion (timpani, mallets, bells, etc.) continues to use
concert pitch span where present.

## Verified cross-family layer (summary)

See ``docs/H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md`` for direct vs derived vs conditional tags.

**Conditional rules** use tessitura / pitch proximity only; there is no transient-envelope
model in this codebase.

**High clarinet ↔ flute** applies only to canonical soprano-line clarinets
(``clarinet``, ``b flat clarinet``, ``a clarinet``, ``c clarinet``).

**Natural horn / cor de chasse ↔ trumpet / bass trumpet** is implemented only for
canonical ``natural horn`` paired with ``trumpet`` or ``bass trumpet``. Valve ``horn`` is
excluded so modern horn↔trumpet similarity is not broadened.
