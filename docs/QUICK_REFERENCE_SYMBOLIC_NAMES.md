# Quick reference: symbolic vocabulary index (H_TI / symbolic inspection)

**Scope:** Canonical instruments, taxonomy families, macrofamily buckets, `TechniqueState` / technique IDs, direction and articulation notes, and other **parser-facing** symbols used by **`H_TI`**, **symbolic inspection**, and the shared timbral pipeline. **Notation-derived only** (MusicXML / music21): **not** audio, **not** PDF/image semantics.

**Consolidated catalogue:** **`docs/Instrumental articulation catalogue.md`** (instruments + aliases from code, `TechniqueState` / articulation dimensions, legacy matrix labels).

**Authoritative tables:** Root **`TECHNICAL_MANUAL.md` — Appendix D** (full canonical instrument + alias sample table, dynamic ladder, harmonic policies, pitch modes, and every symbolic inspection CSV column name). **This file** is a **compact duplicate index** for quick lookup.

**Sources of truth in code:**  
`taxonomy/instrument_taxonomy.py` · `analyzers/hti_taxonomy.py` · `analyzers/technique_state.py` · `analyzers/*_technique.py` · `analyzers/brass_technique.py` · `analyzers/string_technique.py` · `analyzers/percussion_technique.py` · `services/score_audit.py`

---

## 1. Instrument families (`instrument_taxonomy.py`)

| Constant | Value |
|----------|--------|
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

Unmatched part names → canonical **slug of the normalised string**, family **`other`**.

**Policy (not exhaustive in this table):** bare `bass` → `double bass` (strings); bare `alto` / `tenor` / `baritone` → voice roles; many aliases in `_CANONICAL_INSTRUMENTS` (flattened to `_INSTRUMENT_MAP`). See **`TECHNICAL_MANUAL.md` Appendix D.4** for desk labels, `cb` vs `cbcl`, short-token rules, and clarinet transposition rows.

---

## 1b. Macrofamilies (`hti_taxonomy.py`)

`macrofamily_from_instrumental_subfamily` maps each instrumental subfamily (`family` string on events) to a coarse bucket for **`macrofamily_uniformity`** diagnostics:

| `macrofamily` | Instrumental subfamilies (`family`) grouped into this bucket |
|---------------|----------------------------------------------------------------|
| `strings` | `strings` |
| `woodwinds` | `flutes`, `recorders`, `oboes`, `clarinets`, `bassoons`, `saxophones` |
| `brass` | `brass` |
| `percussion` | `percussion` |
| `keyboards` | `keyboard` |
| `voice` | `voice` |
| `other` | `other`, unknown, or empty |

---

## 2. Canonical instruments (unique `(family, canonical)` from `_CANONICAL_INSTRUMENTS` / `_INSTRUMENT_MAP`)

Grouped by family as in the code (order alphabetical within group).

### `strings`

`banjo`, `baryton`, `bass guitar`, `cello`, `cittern`, `double bass`, `dulcimer`, `erhu`, `guitar`, `guzheng`, `harp`, `koto`, `lute`, `mandola`, `mandolin`, `pipa`, `shamisen`, `sitar`, `theorbo`, `ukulele`, `vihuela`, `viol`, `viola`, `viola da gamba`, `violin`, `zither`

### `flutes`

`alto flute`, `bansuri`, `bass flute`, `dizi`, `fife`, `flute`, `ocarina`, `pan flute`, `piccolo`, `shakuhachi`, `tin whistle`

### `recorders`

`alto recorder`, `bass recorder`, `recorder`, `sopranino recorder`, `soprano recorder`, `tenor recorder`

### `oboes`

`bass oboe`, `cor anglais`, `duduk`, `heckelphone`, `musette`, `oboe`, `oboe d'amore`, `oboe da caccia`, `shawm`, `suona`

### `clarinets`

`a clarinet`, `alto clarinet`, `b flat clarinet`, `bass clarinet`, `basset clarinet`, `basset horn`, `c clarinet`, `clarinet`, `contrabass clarinet`, `e flat clarinet`

### `bassoons`

`bassoon`, `contrabassoon`, `crumhorn`, `dulcian`, `racket`

### `saxophones`

`alto saxophone`, `baritone saxophone`, `bass saxophone`, `saxophone` (generic), `sopranino saxophone`, `soprano saxophone`, `tenor saxophone`

### `brass`

`alphorn`, `alto trombone`, `bass trombone`, `bass trumpet`, `bugle`, `cimbasso`, `contrabass trombone`, `cornet`, `cornett`, `didgeridoo`, `euphonium`, `flugelhorn`, `horn`, `mellophone`, `natural horn`, `ophicleide`, `piccolo trumpet`, `serpent`, `sousaphone`, `trombone`, `trumpet`, `tuba`, `wagner tuba`

### `keyboard`

`accordion`, `bandoneon`, `celesta`, `clavichord`, `clavinet`, `concertina`, `fortepiano`, `harmonica`, `harmonium`, `harpsichord`, `organ`, `piano`, `spinet`, `synthesizer`, `virginal`

### `percussion`

`bass drum`, `bongos`, `cajón`, `castanets`, `claves`, `congas`, `cowbell`, `crotales`, `cymbal`, `djembe`, `glockenspiel`, `gong`, `marimba`, `percussion`, `rototom`, `snare drum`, `steelpan`, `suspended cymbal`, `tabla`, `tam-tam`, `tambourine`, `temple block`, `timpani`, `tom-tom`, `triangle`, `tubular bells`, `vibraphone`, `wind chimes`, `wood block`, `xylophone`

### `voice`

`alto`, `baritone`, `bass`, `choir`, `contralto`, `countertenor`, `mezzo-soprano`, `soprano`, `tenor`, `voice`

*(Many **aliases** map onto the above; only canonical names appear in timbral events’ `instrument` field after `get_instrument_and_family`.)*

---

## 3. `TechniqueState` dimensions & IDs (`technique_state.py`)

`technique_state_id(instrument, family, state)` builds strings such as `horn|open`, `violin|arco|sul_pont`, `clarinet|bisbigliando`, `suspended cymbal|let_ring`.

### Brass (`FAMILY_BRASS`)

| Field | Typical values |
|--------|----------------|
| `primary` | `open`, `stopped`, `half_stopped`, `cuivre` |
| `mute` | `none`, `muted_generic`, `straight_mute`, `cup_mute`, `harmon_mute`, `harmon_stem_in`, `harmon_stem_out`, `bucket_mute`, `plunger`, `practice_mute` |
| `articulation_effect` | `none`, `flutter` |

**Note:** Isolated `+` (or explicit “plus sign”) in **brass** direction text can set `stopped` (project heuristic).

**music21 articulations** merged on notes: `articulations.Stopped` → stopped primary; `articulations.Tremolo` (expressions) → brass flutter where wired.

### Bowed strings (`FAMILY_STRINGS`, violin / viola / cello / double bass)

| Field | Typical values |
|--------|----------------|
| `excitation` | `arco`, `pizz`, `snap_pizz`, `col_legno_battuto`, `col_legno_tratto`, `tremolo`, … (also sul-g / sul-d style strings normalised from text) |
| `mute` | `none`, `muted` |
| `contact_point` | `ordinary`, `sul_pont`, `molto_sul_pont`, `sul_tasto`, `molto_sul_tasto`, `behind_bridge`, `on_bridge`, `sub_ponticello` |
| `articulation_effect` | `none`, `tremolo` |
| `special` | e.g. `harmonic:natural_harmonic`, `harmonic:artificial_harmonic`, `harmonic:harmonic_generic`, `pressure:…` |

**music21:** `Pizzicato`, `SnapPizzicato`, `NailPizzicato`, `FrettedPluck`, `StringHarmonic`, `Harmonic`, `Stopped` (mute), `Tremolo` (expression); **notehead** `diamond` / `Diamond` → harmonic hint when no harmonic already set.

### Winds (`FAMILY_FLUTES`, `FAMILY_CLARINETS`, `FAMILY_OBOES`, `FAMILY_BASSOONS`, `FAMILY_SAXOPHONES`)

`primary` / wind lane (stored in `TechniqueState.primary` for winds):

`ordinario`, `bisbigliando`, `flutter`, `slap`, `key_click`, `air_sound`, `multiphonic`, `jet_whistle`, `whistle_tone`, `growl`, `subtone`, `singing_and_playing`, `harmonic` (from note `Harmonic` articulation)

### Percussion (`FAMILY_PERCUSSION`)

| Field | Typical values |
|--------|----------------|
| `primary` (beater / lane) | `ordinary`, `hard_mallet`, `yarn_mallet`, `felt_mallet`, `soft_mallet`, `brushes`, `bow`, `superball`, … |
| `excitation` / stroke | `ordinary`, `bowed`, `roll`, `rimshot`, `rim`, `edge`, … |
| `resonance` | `open`, `let_ring`, `damped`, `choke` |

---

## 4. Legacy / matrix technique labels (per-module constants)

### `brass_technique.py`

`open`, `straight_mute`, `cup_mute`, `harmon_mute`, `bucket_mute`, `stopped`, `half_stopped`, `cuivre`, `flutter`, `muted_generic`, `unknown`

### `string_technique.py`

`arco`, `tremolo`, `sul_pont`, `sul_tasto`, `harmonic`, `muted`, `pizz`, `unknown`

### `flute_technique.py`

`ordinario`, `vibrato`, `breathy`, `flutter`, `harmonic`, `whistle`, `air_keys`, `unknown`

### `clarinet_technique.py`

`ordinario`, `light_vibrato`, `flutter`, `breathy`, `slap`, `multiphonic`, `unknown`

### `double_reed_technique.py`

`ordinario`, `flutter`, `multiphonic`, `breathy`, `unknown`

### `saxophone_technique.py`

`ordinario`, `subtone`, `growl`, `flutter`, `slap`, `breathy`, `overtone_special`, `unknown`

### `percussion_technique.py`

`ordinario`, `mallet_hard`, `mallet_soft`, `mallet_felt`, `mallet_yarn`, `sticks`, `brushes`, `snare_on`, `snare_off`, `damped`, `open`, `rolled`, `bowed`, `vibraphone_pedal`, `vibraphone_no_pedal`, `cymbal_suspended`, `cymbal_crash`, `rim_stroke`, `unknown`

---

## 5. Where text is read from (music21)

Typical objects feeding **keyword** / **direction** parsers:

- **`expressions.TextExpression`**, **`expressions.RehearsalMark`**, **`dynamics.Dynamic`** (part scan order in `iter_timbral_elements`)
- **`notation_context.notation_text_context_for_note`** — note-local text; optional same-measure directions **before** the note’s offset (`prior`) or legacy whole-measure merge; timbral uses `none` + chronological directions
- **Articulations** on **`note.Note`** / **`chord.Chord`** members: e.g. `articulations.Stopped`, `articulations.Pizzicato`, `articulations.Harmonic`, `articulations.StringHarmonic`, `articulations.SnapPizzicato`, …
- **Notehead** name on **`note.Note`** (e.g. diamond → string harmonic heuristic)

---

## 6. Keeping this file accurate

When you add instruments or technique tokens:

1. Update `_CANONICAL_INSTRUMENTS` (aliases per canonical instrument) and/or `technique_state.py` / `*_technique.py`.
2. Regenerate / refresh **`TECHNICAL_MANUAL.md` Appendix D** (canonical table and glossary) — this quick index should stay aligned with that appendix.
3. Extend **§3–4** here if new technique dimensions or per-module constants appear.

*Alias spellings are not duplicated exhaustively here—see `instrument_taxonomy.py` and Appendix D.*
