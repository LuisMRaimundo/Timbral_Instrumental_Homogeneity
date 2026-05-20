## Appendix D — Symbolic vocabularies recognised by the analyser

**Scope warning (read first):** The lists below describe what the **current** analyser recognises or exports from **music21** MusicXML/MIDI parses. They are **not** a universal catalogue of all musical techniques or all MusicXML possibilities. **Exporter behaviour** (Dorico, Sibelius, MuseScore, …) and **music21** version differences can still change which objects appear, which articulation classes are attached, and which free-text directions survive import.

**Sources of truth in code:** `taxonomy/instrument_taxonomy.py`, `analyzers/hti_taxonomy.py`, `analyzers/technique_state.py`, `analyzers/pitch_interpretation.py`, `analyzers/harmonic_pitch.py`, `analyzers/hti_dynamics.py`, `analyzers/hti.py` (technique coverage + CSV columns), `services/score_audit.py` (symbolic inspection column tuples).

A compact duplicate index lives in **`docs/QUICK_REFERENCE_SYMBOLIC_NAMES.md`**.

### D.1 Canonical instruments

Each row is one key in `_CANONICAL_INSTRUMENTS` in `instrument_taxonomy.py`. The **`instrumental_subfamily`** column is the taxonomy `family` constant (`FAMILY_*`). **`macrofamily`** is `macrofamily_from_instrumental_subfamily` in `hti_taxonomy.py`. **Aliases** in the fourth column are the first few literal alias strings from the same dict entry (ellipsis means more in source).

| `canonical_instrument` | `instrumental_subfamily` (taxonomy `family`) | `macrofamily` | Representative aliases (first few; full list in source) | Notes |
|---|---|---|---|---|
| `a clarinet` | `clarinets` | `woodwinds` | `clarinet in a`, `a clarinet`, `cl in a`, `clarinete em lá`, `clarinete em la` |  |
| `accordion` | `keyboard` | `keyboards` | `accordion`, `acordeão` |  |
| `alphorn` | `brass` | `brass` | `alphorn` |  |
| `alto` | `voice` | `voice` | `alto` |  |
| `alto clarinet` | `clarinets` | `woodwinds` | `alto clarinet` |  |
| `alto flute` | `flutes` | `woodwinds` | `alto flute`, `flauta alto`, `flauta em sol` |  |
| `alto recorder` | `recorders` | `woodwinds` | `alto recorder` |  |
| `alto saxophone` | `saxophones` | `woodwinds` | `alto saxophone`, `alto sax`, `saxofone alto` |  |
| `alto trombone` | `brass` | `brass` | `alto trombone`, `trombone alto` |  |
| `b flat clarinet` | `clarinets` | `woodwinds` | `clarinet in b flat`, `clarinet in bb`, `b flat clarinet`, `bb clarinet`, `cl in bb`, … |  |
| `bandoneon` | `keyboard` | `keyboards` | `bandoneon` |  |
| `banjo` | `strings` | `strings` | `banjo` |  |
| `bansuri` | `flutes` | `woodwinds` | `bansuri` |  |
| `baritone` | `voice` | `voice` | `baritone` |  |
| `baritone saxophone` | `saxophones` | `woodwinds` | `baritone saxophone`, `baritone sax`, `saxofone baritono` |  |
| `baryton` | `strings` | `strings` | `baryton` |  |
| `bass` | `voice` | `voice` | `bass voice` |  |
| `bass clarinet` | `clarinets` | `woodwinds` | `bass clarinet`, `bass cl.`, `bcl`, `clarinete baixo` |  |
| `bass drum` | `percussion` | `percussion` | `bass drum`, `bd`, `bombo` |  |
| `bass flute` | `flutes` | `woodwinds` | `bass flute`, `flauta baixo` |  |
| `bass guitar` | `strings` | `strings` | `bass guitar` |  |
| `bass oboe` | `oboes` | `woodwinds` | `bass oboe` |  |
| `bass recorder` | `recorders` | `woodwinds` | `bass recorder` |  |
| `bass saxophone` | `saxophones` | `woodwinds` | `bass saxophone` |  |
| `bass trombone` | `brass` | `brass` | `bass trombone`, `trombone baixo` |  |
| `bass trumpet` | `brass` | `brass` | `bass trumpet`, `trompete baixo` |  |
| `basset clarinet` | `clarinets` | `woodwinds` | `basset clarinet` |  |
| `basset horn` | `clarinets` | `woodwinds` | `basset horn` |  |
| `bassoon` | `bassoons` | `woodwinds` | `bassoon`, `fagott`, `bn.`, `bsn.`, `fg.`, … |  |
| `bongos` | `percussion` | `percussion` | `bongos`, `bongo` |  |
| `bugle` | `brass` | `brass` | `bugle` |  |
| `c clarinet` | `clarinets` | `woodwinds` | `clarinet in c`, `c clarinet` |  |
| `cajón` | `percussion` | `percussion` | `cajón`, `cajon` |  |
| `castanets` | `percussion` | `percussion` | `castanets` |  |
| `celesta` | `keyboard` | `keyboards` | `celesta`, `celeste`, `cel.` |  |
| `cello` | `strings` | `strings` | `violoncello`, `violoncelo`, `violoncélo`, `cello`, `vc.`, … |  |
| `choir` | `voice` | `voice` | `choir`, `chorus` |  |
| `cimbasso` | `brass` | `brass` | `cimbasso` |  |
| `cittern` | `strings` | `strings` | `cittern` |  |
| `clarinet` | `clarinets` | `woodwinds` | `soprano clarinet`, `clarinet`, `clarinete`, `cl.`, `cl` |  |
| `claves` | `percussion` | `percussion` | `claves` |  |
| `clavichord` | `keyboard` | `keyboards` | `clavichord` |  |
| `clavinet` | `keyboard` | `keyboards` | `clavinet` |  |
| `concertina` | `keyboard` | `keyboards` | `concertina` |  |
| `congas` | `percussion` | `percussion` | `congas`, `conga` |  |
| `contrabass clarinet` | `clarinets` | `woodwinds` | `contrabass clarinet`, `cbcl`, `clarinete contrabaixo` |  |
| `contrabass trombone` | `brass` | `brass` | `contrabass trombone`, `trombone contrabaixo` |  |
| `contrabassoon` | `bassoons` | `woodwinds` | `contrabassoon`, `contrabassoon in f`, `cfg.`, `cbn`, `contrafagote`, … | Octave-down concert handling in `xml_pitch_as_real_with_octave_transposers` (`pitch_interpretation.py`). |
| `contralto` | `voice` | `voice` | `contralto` |  |
| `cor anglais` | `oboes` | `woodwinds` | `cor anglais`, `english horn`, `cor inglês`, `cor ingles`, `corno inglese` |  |
| `cornet` | `brass` | `brass` | `cornet`, `cornetto`, `corneta`, `cornetim` |  |
| `cornett` | `brass` | `brass` | `cornett` |  |
| `countertenor` | `voice` | `voice` | `countertenor` |  |
| `cowbell` | `percussion` | `percussion` | `cowbell` |  |
| `crotales` | `percussion` | `percussion` | `crotales` |  |
| `crumhorn` | `bassoons` | `woodwinds` | `crumhorn` |  |
| `cymbal` | `percussion` | `percussion` | `cymbal`, `cymbals`, `pratos` |  |
| `didgeridoo` | `brass` | `brass` | `didgeridoo` |  |
| `dizi` | `flutes` | `woodwinds` | `dizi` |  |
| `djembe` | `percussion` | `percussion` | `djembe` |  |
| `double bass` | `strings` | `strings` | `double bass`, `contrabass`, `cb.`, `cb`, `db.`, … | Octave-down concert handling in `xml_pitch_as_real_with_octave_transposers` (`pitch_interpretation.py`). |
| `duduk` | `oboes` | `woodwinds` | `duduk` |  |
| `dulcian` | `bassoons` | `woodwinds` | `dulcian`, `dulciana` |  |
| `dulcimer` | `strings` | `strings` | `dulcimer` |  |
| `e flat clarinet` | `clarinets` | `woodwinds` | `clarinet in e flat`, `clarinet in eb`, `e flat clarinet`, `eb clarinet`, `cl in eb`, … |  |
| `erhu` | `strings` | `strings` | `erhu` |  |
| `euphonium` | `brass` | `brass` | `baritone horn`, `euphonium`, `eufónio`, `eufonio`, `bombardino` |  |
| `fife` | `flutes` | `woodwinds` | `fife` |  |
| `flugelhorn` | `brass` | `brass` | `flugelhorn`, `fliscorne` |  |
| `flute` | `flutes` | `woodwinds` | `flute`, `traverso`, `fl.`, `fl`, `flauta`, … |  |
| `fortepiano` | `keyboard` | `keyboards` | `fortepiano` |  |
| `glockenspiel` | `percussion` | `percussion` | `glockenspiel`, `orchestral bells`, `glock.` |  |
| `gong` | `percussion` | `percussion` | `gong` |  |
| `guitar` | `strings` | `strings` | `acoustic guitar`, `electric guitar`, `classical guitar`, `guitar`, `guitarra` |  |
| `guzheng` | `strings` | `strings` | `guzheng` |  |
| `harmonica` | `keyboard` | `keyboards` | `harmonica` |  |
| `harmonium` | `keyboard` | `keyboards` | `harmonium` |  |
| `harp` | `strings` | `strings` | `harp`, `hp.`, `harpa` |  |
| `harpsichord` | `keyboard` | `keyboards` | `harpsichord`, `cravo` |  |
| `heckelphone` | `oboes` | `woodwinds` | `heckelphone`, `heckelfone` |  |
| `horn` | `brass` | `brass` | `french horn`, `horn`, `hn.`, `hn`, `trompa`, … |  |
| `koto` | `strings` | `strings` | `koto` |  |
| `lute` | `strings` | `strings` | `lute` |  |
| `mandola` | `strings` | `strings` | `mandola` |  |
| `mandolin` | `strings` | `strings` | `mandolin` |  |
| `marimba` | `percussion` | `percussion` | `marimba` |  |
| `mellophone` | `brass` | `brass` | `mellophone` |  |
| `mezzo-soprano` | `voice` | `voice` | `mezzo-soprano`, `mezzo soprano` |  |
| `musette` | `oboes` | `woodwinds` | `musette` |  |
| `natural horn` | `brass` | `brass` | `cor de chasse`, `hunting horn`, `natural horn`, `trompa natural` |  |
| `oboe` | `oboes` | `woodwinds` | `oboe`, `ob.`, `ob`, `oboé` |  |
| `oboe d'amore` | `oboes` | `woodwinds` | `oboe d'amore`, `oboé d'amore`, `oboe de amor`, `oboe d amore`, `oboe damore` |  |
| `oboe da caccia` | `oboes` | `woodwinds` | `oboe da caccia` |  |
| `ocarina` | `flutes` | `woodwinds` | `ocarina` |  |
| `ophicleide` | `brass` | `brass` | `ophicleide` |  |
| `organ` | `keyboard` | `keyboards` | `organ`, `pipe organ`, `org.`, `órgão`, `orgao` |  |
| `pan flute` | `flutes` | `woodwinds` | `pan flute`, `pan pipes` |  |
| `percussion` | `percussion` | `percussion` | `percussion`, `drums`, `drum set`, `drum kit`, `perc.`, … |  |
| `piano` | `keyboard` | `keyboards` | `grand piano`, `upright piano`, `electric piano`, `piano`, `pf.`, … |  |
| `piccolo` | `flutes` | `woodwinds` | `piccolo`, `picc.`, `picc`, `flautim`, `ottavino` |  |
| `piccolo trumpet` | `brass` | `brass` | `piccolo trumpet`, `trompete piccolo` |  |
| `pipa` | `strings` | `strings` | `pipa` |  |
| `racket` | `bassoons` | `woodwinds` | `racket` |  |
| `recorder` | `recorders` | `woodwinds` | `recorder`, `blockflöte`, `block flute` |  |
| `rototom` | `percussion` | `percussion` | `rototom` |  |
| `saxophone` | `saxophones` | `woodwinds` | `saxophone`, `sax` |  |
| `serpent` | `brass` | `brass` | `serpent` |  |
| `shakuhachi` | `flutes` | `woodwinds` | `shakuhachi` |  |
| `shamisen` | `strings` | `strings` | `shamisen` |  |
| `shawm` | `oboes` | `woodwinds` | `shawm` |  |
| `sitar` | `strings` | `strings` | `sitar` |  |
| `snare drum` | `percussion` | `percussion` | `snare drum`, `sd`, `caixa clara`, `tarola` |  |
| `sopranino recorder` | `recorders` | `woodwinds` | `sopranino recorder` |  |
| `sopranino saxophone` | `saxophones` | `woodwinds` | `sopranino saxophone` |  |
| `soprano` | `voice` | `voice` | `soprano` |  |
| `soprano recorder` | `recorders` | `woodwinds` | `soprano recorder` |  |
| `soprano saxophone` | `saxophones` | `woodwinds` | `soprano saxophone` |  |
| `sousaphone` | `brass` | `brass` | `sousaphone` |  |
| `spinet` | `keyboard` | `keyboards` | `spinet` |  |
| `steelpan` | `percussion` | `percussion` | `steelpan`, `steel drum` |  |
| `suona` | `oboes` | `woodwinds` | `suona` |  |
| `suspended cymbal` | `percussion` | `percussion` | `suspended cymbal`, `prato suspenso` |  |
| `synthesizer` | `keyboard` | `keyboards` | `synthesizer`, `synth`, `sintetizador`, `synth.` |  |
| `tabla` | `percussion` | `percussion` | `tabla` |  |
| `tam-tam` | `percussion` | `percussion` | `tam-tam`, `tamtam` |  |
| `tambourine` | `percussion` | `percussion` | `tambourine` |  |
| `temple block` | `percussion` | `percussion` | `temple block` |  |
| `tenor` | `voice` | `voice` | `tenor` |  |
| `tenor recorder` | `recorders` | `woodwinds` | `tenor recorder` |  |
| `tenor saxophone` | `saxophones` | `woodwinds` | `tenor saxophone`, `tenor sax`, `saxofone tenor` |  |
| `theorbo` | `strings` | `strings` | `theorbo` |  |
| `timpani` | `percussion` | `percussion` | `timpani`, `kettledrum`, `timp.`, `tímpanos`, `timpanos` |  |
| `tin whistle` | `flutes` | `woodwinds` | `tin whistle` |  |
| `tom-tom` | `percussion` | `percussion` | `tom-tom`, `tom tom` |  |
| `triangle` | `percussion` | `percussion` | `triangle`, `tgl`, `triângulo` |  |
| `trombone` | `brass` | `brass` | `tenor trombone`, `soprano trombone`, `sackbut`, `trombone`, `trb.`, … |  |
| `trumpet` | `brass` | `brass` | `natural trumpet`, `trumpet`, `tpt.`, `trp.`, `tr.`, … |  |
| `tuba` | `brass` | `brass` | `bass tuba`, `tuba`, `tba.` |  |
| `tubular bells` | `percussion` | `percussion` | `tubular bells`, `chimes` |  |
| `ukulele` | `strings` | `strings` | `ukulele` |  |
| `vibraphone` | `percussion` | `percussion` | `vibraphone`, `vibes`, `vib.`, `vibrafone` |  |
| `vihuela` | `strings` | `strings` | `vihuela` |  |
| `viol` | `strings` | `strings` | `viol` |  |
| `viola` | `strings` | `strings` | `viola`, `vla.`, `va.`, `viola de arco` |  |
| `viola da gamba` | `strings` | `strings` | `viola da gamba` |  |
| `violin` | `strings` | `strings` | `violin`, `vln.`, `vn.`, `vl.`, `violino`, … |  |
| `virginal` | `keyboard` | `keyboards` | `virginal` |  |
| `voice` | `voice` | `voice` | `voice`, `vocals` |  |
| `wagner tuba` | `brass` | `brass` | `wagner tuba`, `tuba wagneriana` |  |
| `wind chimes` | `percussion` | `percussion` | `wind chimes` |  |
| `wood block` | `percussion` | `percussion` | `wood block` |  |
| `xylophone` | `percussion` | `percussion` | `xylophone`, `xyl.`, `xilofone` |  |
| `zither` | `strings` | `strings` | `zither` |  |

**Unknown mapping:** when no alias matches, `resolve_instrument_taxonomy` returns a normalised slug and `family` **`other`** (see docstring in `instrument_taxonomy.py`).

### D.2 Instrumental subfamilies (taxonomy `family`)

Exact string values from `instrument_taxonomy.py`:

| Constant | Value stored on events / exports |
|----------|-----------------------------------|
| `FAMILY_STRINGS` | `strings` |
| `FAMILY_FLUTES` | `flutes` |
| `FAMILY_RECORDERS` | `recorders` |
| `FAMILY_OBOES` | `oboes` |
| `FAMILY_CLARINETS` | `clarinets` |
| `FAMILY_BASSOONS` | `bassoons` |
| `FAMILY_SAXOPHONES` | `saxophones` |
| `FAMILY_BRASS` | `brass` |
| `FAMILY_KEYBOARD` | `keyboard` |
| `FAMILY_PERCUSSION` | `percussion` |
| `FAMILY_VOICE` | `voice` |
| `FAMILY_OTHER` | `other` |

### D.3 Macrofamilies (H_TI diagnostic)

`macrofamily_from_instrumental_subfamily` maps each instrumental subfamily to exactly one of:

`strings`, `woodwinds`, `brass`, `percussion`, `keyboards`, `voice`, `other`

(`woodwinds` aggregates flutes, recorders, oboes, clarinets, bassoons, saxophones.)

### D.4 Instrument alias and desk-label rules

Documented in the **module docstring** and helpers in `instrument_taxonomy.py`:

- **String desk labels** — `match_string_section_desk_label` recognises short section/desk phrases (e.g. violin/viola/cello/double-bass tokens + optional Roman numerals + stand numbers) and sets `section_label` / `desk_group` in orchestration columns (`orchestration_label_fields`).
- **Bare `bass`** → **`double bass`** (string section default). Use **`bass voice`** for vocal bass (`canonical_instrument` **`bass`** in voice family).
- **Bare `alto` / `tenor` / `baritone`** → **voice** roles, not saxophone or baritone horn without additional tokens.
- **`cb` / `cb.`** → **double bass** in string context; **`cbcl`** is **contrabass clarinet**.
- **`cornetto`** maps to modern brass **cornet**; historical **`cornett`** remains its own canonical instrument.
- **Short tokens** (`fl`, `cl`, `bd`, …) only match when the normalised part name is a **short score-like phrase** (≤ `_SHORT_ALIAS_MAX_TOKENS` words) so mid-sentence matches are avoided.
- **Clarinet transpositions** — separate canonical rows: `b flat clarinet`, `a clarinet`, `e flat clarinet`, `c clarinet`, generic `clarinet`, etc., each with its own alias list.
- **Octave transposers** — see **D.11** for `double bass` and `contrabassoon` in `xml_pitch_as_real_with_octave_transposers`.

### D.5 Technique state model (`TechniqueState`)

The merged playing-state object (`technique_state` dict on events) is defined in `technique_state.py` (`TechniqueState` dataclass). **Field names** (all string-valued except `special`):

`family`, `instrument`, `primary`, `mute`, `contact_point`, `excitation`, `articulation_effect`, `resonance`, `noise_component`, `pressure`, `beater`, `stroke`, `special` (tuple of extra tags, e.g. `harmonic:…`).

**Family-specific behaviour (examples, not exhaustive):**

- **Brass** — `primary` may include `open`, `stopped`, `cuivre`, `half_stopped`, `vibrato`, …; `mute` includes harmon-mute stem variants and straight / cup / bucket names resolved in brass technique helpers; `articulation_effect` captures notated brass articulations when parsed.
- **Bowed strings** (`violin`, `viola`, `cello`, `double bass`) — `excitation` distinguishes `arco`, `pizz`, `snap_pizz`, `col_legno`, `tremolo`, …; `contact_point` encodes sul ponticello / sul tasto / flautando-style text; `mute` con sordino; harmonics via `special` entries `harmonic:…` and `pressure:…` from `harmonic_dim` / `pressure_dim`.
- **Woodwinds / saxophones** — `primary` lane (`ordinario`, flutter-tongue, double-tongue, etc. when present) plus `articulation_effect` and `special`.
- **Percussion** — `resonance`, `beater`, `stroke`, `articulation_effect`, `special`.

**`technique_state_id`** — stable **per-event** fingerprint used in overlap distributions: built by `technique_state_id(instrument, family, state)` (see docstring for examples such as `horn|open`, `violin|arco|sul_ponticello`, …).

### D.6 `technique_uniformity_key` and related audit columns

- **`technique_uniformity_key`** — instrument-free bucket for **Herfindahl `technique_uniformity`** and audit (`compute_technique_uniformity_key` / `compute_technique_uniformity_key_from_event`). When `has_special_explicit_technique` is false, the key is the constant **`ordinary_default`** (`ORDINARY_DEFAULT_UNIFORMITY_KEY`). Otherwise it is derived from the **tail** of `technique_state_id` (instrument prefix dropped), with normalisation in `_UNIFORMITY_TAIL_ALIASES` (e.g. `sul_pont` → `sul_ponticello`, `pizz` → `pizzicato`, …) and con/senza sordino slug folding.
- **`technique_state_id`** — full fingerprint including instrument (see D.5).
- **`explicit_technique`** — audit column from `explicit_technique_audit_label`: human token equal to the uniformity key when explicit, else **`none`**.
- **`explicit_technique_detected`** — boolean (`explicit_technique_detected` / `event_has_special_explicit_technique`): whether the event carries **contrasting** notated technique beyond defaults (so the technique Herfindahl sees a non-`ordinary_default` bucket).

**Closed set:** only **`ordinary_default`** is guaranteed constant. **All other keys** are **open-ended** compositional strings produced by the parser from score text and music21 objects.

**`technique_coverage_status` (window-level, `hti.py`):** `unavailable`, `ambiguous`, `ordinary_default_uniform`, `explicit_uniform`, `explicit_mixed`.

### D.7 Articulations

- **Event audit `articulation_marks` column** — `score_audit._articulation_names` joins `type(art).__name__` for each object in `note.articulations` after music21 import. This is an **open set** of music21 class names (e.g. `Staccato`, `Tenuto`, …) depending on what the exporter encodes.
- **No separate static whitelist** is enforced in `score_audit.py` for articulations beyond what music21 attaches.
- **Technique merge** — many playing-style directions are **not** articulation classes; they are absorbed via `notation_context` / `TechniqueStateContext` when scanning directions (see `technique_state.py` and related `*_technique.py` modules). Those affect **`TechniqueState`** fields rather than `articulation_marks`.

### D.8 Technical marks, text, noteheads, and effect breakout columns

Event-audit columns (see `SCORE_AUDIT_EVENT_COLUMNS` in `score_audit.py`):

| Column | Meaning / derivation |
|--------|----------------------|
| `articulation_marks` | Comma-separated music21 articulation class names (D.7). |
| `technical_marks` | Technical indications collected on the timbral event (`technical_marks` field from the timbral pipeline — exporter-dependent). |
| `expression_text` | Expression text objects relevant to the note (music21). |
| `direction_text` | Parsed direction / technique text snapshot on the event. |
| `notehead_type` | music21 notehead string when present (e.g. `diamond`, `normal`; exporter-dependent). |
| `mute_state` | From `TechniqueState.mute` (`_technique_breakout`). |
| `sordino_state` | Copy of mute when non-`none`, else `none`. |
| `pizz_arco_state` | From `excitation` (string) or `unknown`. |
| `sul_ponticello_state` | Parsed from `contact_point` text containing sul pont / sul ponticello markers. |
| `sul_tasto_state` | Parsed from sul tasto markers in `contact_point`. |
| `technique_harmonic_marker` | `special` entry beginning `harmonic:` when present, else `none`. |
| `tremolo_state` | `yes` / effect string when tremolo detected from `articulation_effect`, `excitation`, or `special`. |
| `stopped_open_cuivre_state` | Brass `primary` when in `stopped`, `open`, `cuivre`, `half_stopped`. |
| `vibrato_state` | `yes` when brass `primary` is `vibrato`. |
| `other_effects` | Concatenation of remaining `special` strings and non-`none` `articulation_effect` when not captured above. |

Values are **symbolic strings** after merge; they are **not** normalised to a finite global enum except where noted.

### D.9 Dynamics (ordinal ladder and aggregates)

**Primary ladder** `NOTATED_DYNAMIC_SYMBOLIC_ORDINAL` in `hti_dynamics.py` (token → symbolic intensity in **[0, 1]**, not SPL):

| Token | Ordinal |
|-------|--------|
| `pppp` | 0.00 |
| `ppp` | 0.08 |
| `pp` | 0.16 |
| `p` | 0.30 |
| `mp` | 0.43 |
| `mf` | 0.55 |
| `f` | 0.72 |
| `ff` | 0.88 |
| `fff` | 0.96 |
| `ffff` | 1.00 |

**Secondary tokens** `_SECONDARY_ORDINAL` map conservatively onto the same ladder (`mpp`, `mfp`, `nf`, `fp`, `sf`, `sfp`, `sfz`, `sffz`, `fz`, `rf`, `sp`, `sfzp`, `n`).

**Dynamic parsing** for single-token extraction uses `_STANDARD_DYNAMIC_MARKS` in `technique_state.parse_standard_dynamic_mark` (longest-first search input).

**Exports / aggregates (`aggregate_notated_dynamics_for_window`):**

- `notated_dynamic_level_distribution` — overlap shares per parsed class; includes **`__unknown__`** when overlap mass has no recognised mark.
- `notated_dynamic_coherence` — Herfindahl on **known** marks only (unknown excluded from the sum).
- `dynamic_coverage_status` — `explicit` (known mass at least **72%** of total), `partial` (at least **8%**), else `unavailable`.
- `dynamic_divergence_detected` — `True` when **at least two** distinct known dynamic classes each carry **at least 12%** of **total** window overlap mass.
- Hairpins — boolean flags `crescendo_active` / `diminuendo_active` when any active event carries `hairpin` `crescendo` / `diminuendo`.

### D.10 Harmonic vocabulary

**Policies** (`harmonic_pitch.py`, `normalize_harmonic_pitch_policy`): `conservative`, `infer_common_artificial`, `written_as_sounding`.

**Artificial interval rule ids** (`ARTIFICIAL_STRING_HARMONIC_INTERVALS` keys, also `harmonic_interval_rule_id`): `octave`, `perfect_fifth`, `perfect_fourth`, `major_third`, `minor_third`.

**Numeric constant:** `INTERVAL_MATCH_TOLERANCE_SEMITONES = 0.25` for artificial table matching.

**Per-tone harmonic columns** (`SCORE_AUDIT_HARMONIC_PITCH_COLUMNS` in `score_audit.py`): `harmonic_state`, `harmonic_type`, `harmonic_pitch_role`, `harmonic_detection_source`, `harmonic_base_pitch`, `harmonic_base_midi`, `harmonic_touching_pitch`, `harmonic_touching_midi`, `harmonic_touching_interval_semitones`, `harmonic_interval_rule_id`, `harmonic_sounding_pitch`, `harmonic_sounding_midi`, `harmonic_sounding_status`, `harmonic_pitch_policy`, `harmonic_warning`.

**Representative `harmonic_state` / `harmonic_type` / `harmonic_sounding_status` values** produced by `harmonic_pitch.py` include at least: `none`, `natural`, `artificial`, `harmonic_candidate`, `unresolved`, `explicit`, `inferred_common_artificial`, `unavailable` (exact combinations depend on MusicXML `StringHarmonic` / notehead data). Warnings include the module constants for diamond noteheads on strings vs non-strings.

### D.11 Pitch interpretation vocabulary

**Modes** (`PITCH_INTERPRETATION_MODES` in `pitch_interpretation.py`):

- `musicxml_sounding` — apply part `transposition` when present.
- `xml_pitch_as_real` — treat written pitch as concert; no transposition.
- `ignore_octave_transpositions_only` — chromatic part of transposition only.
- `xml_pitch_as_real_with_octave_transposers` — concert pitch for most instruments, but apply stored octave transposition for canonical **`double bass`** and **`contrabassoon`** (`_OCTAVE_DOWN_CONCERT_CANONICAL`).

**Per-tone transpose audit fields** (from `interpret_pitch_tone` / `compute_effective_alter`): `raw_written_pitch`, `raw_written_midi`, `effective_written_midi`, `effective_sounding_midi`, `chromatic_transpose_detected`, `octave_transpose_detected`, `chromatic_transpose_applied`, `octave_transpose_applied`, `total_transpose_applied`, `transpose_applied`, `pitch_interpretation_mode`, `raw_xml_alter`, `effective_alter`, `microtonal_accidental_detected`, `microtonal_accidental_status` (`none` / `inferred_from_text` / `explicit_natural` / `unknown` from `compute_effective_alter`).

### D.12 Percussion vocabulary

**Ontology pitch status** (`PercussionMeta.pitch_status` enum in `percussion_ontology.py`): `pitched`, `quasi_pitched`, `unpitched`.

**Symbolic inspection / H_TI register:** inventory column `percussion_pitch_status` records that ontology status for canonical percussion instruments. **Register compactness** skips unpitched percussion hits when building pitch lists (same rule as timbral register extraction: percussion-family + `UNPITCHED` status does not contribute sounding MIDI rows to span/pairwise terms).

### D.13 Symbolic inspection field glossary

Column order is **normative** for CSV exports (`SCORE_AUDIT_*_COLUMN` tuples in `score_audit.py`). **Inventory** = per-part rollup; **event** = one row per chord tone / unpitched hit; **vertical** = simultaneous slice at a quantised offset.

| Field | Table | Meaning | Source / notes |
|-------|-------|---------|----------------|
| `part_index` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `part_id` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `part_name` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `raw_part_name` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `section_label` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `desk_group` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `part_label_original` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `staff_name` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `raw_instrument_name` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `music21_instrument_class` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `canonical_instrument` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `instrumental_subfamily` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `macrofamily` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `transposition` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `sounding_pitch_policy` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `is_percussion` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `percussion_pitch_status` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `pitched_or_unpitched` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `number_of_events` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `number_of_pitched_events` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `number_of_unpitched_events` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `dynamic_marks_found` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `technique_marks_found` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `articulation_marks_found` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `effect_marks_found` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `warnings` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `unresolved_or_ambiguous_mapping` | instrument inventory | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `measure` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `offset_quarterLength` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `duration_quarterLength` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `part_index` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `part_id` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `part_name` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `raw_part_name` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `section_label` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `desk_group` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `part_label_original` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `canonical_instrument` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `instrumental_subfamily` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `macrofamily` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `written_pitch` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `written_midi` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `sounding_pitch` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `sounding_midi` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `octave` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `raw_xml_alter` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `accidental_text` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `microtonal_accidental_detected` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `effective_alter` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `raw_written_pitch` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `raw_written_midi` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `effective_written_midi` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `effective_sounding_midi` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `chromatic_transpose_detected` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `octave_transpose_detected` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `chromatic_transpose_applied` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `octave_transpose_applied` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `total_transpose_applied` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `transpose_applied` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `pitch_interpretation_mode` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `microtonal_accidental_status` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `chord_id` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `chord_tone_index` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `is_chord_tone` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `is_unpitched` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `dynamic_mark` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `active_dynamic` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `crescendo_active` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `diminuendo_active` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `explicit_technique` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `explicit_technique_detected` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `technique_uniformity_key` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `technique_state_id` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `technique_state_summary` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `articulation_marks` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `technical_marks` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `expression_text` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `direction_text` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `notehead_type` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_state` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_type` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_pitch_role` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_detection_source` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_base_pitch` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_base_midi` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_touching_pitch` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_touching_midi` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_touching_interval_semitones` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_interval_rule_id` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_sounding_pitch` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_sounding_midi` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_sounding_status` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_pitch_policy` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_warning` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `mute_state` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `sordino_state` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `pizz_arco_state` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `sul_ponticello_state` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `sul_tasto_state` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `technique_harmonic_marker` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `tremolo_state` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `stopped_open_cuivre_state` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `vibrato_state` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `other_effects` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `parser_warning` | event audit | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `measure` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `offset_quarterLength` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `active_part_names` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `active_canonical_instruments` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `active_instrumental_subfamilies` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `active_macrofamilies` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `written_pitches` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `sounding_pitches` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `sounding_midi_values` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `number_of_active_events` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `number_of_active_pitched_events` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `number_of_active_unpitched_events` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `vertical_pitch_cardinality` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `register_span_semitones` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `register_span_proximity` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `pairwise_interval_proximity` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `register_compactness` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `active_dynamic_distribution` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `dominant_dynamic` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `active_technique_states` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `technique_coverage_status` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `articulation_summary` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `effect_summary` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `warnings` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_summary` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `harmonic_unresolved_count` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `n_unique_sounding_midis` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `midi_multiset` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `midi_set` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |
| `duplicate_pitch_count` | vertical sonorities | Exported audit field; construction is in `services/score_audit.py` (search for the quoted field key in that module together with `TimbralHomogeneityAnalyzer` events). | `score_audit.py` |

---
