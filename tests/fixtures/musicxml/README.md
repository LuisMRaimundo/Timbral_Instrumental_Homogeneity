# Symbolic MusicXML corpus (tests)

Small **synthetic** MusicXML 3.1 files used to validate the timbral pipeline **after** `music21` import (same path as production: `parse_score` → `TimbralHomogeneityAnalyzer`).

## Exporter / importer limitations

- **Directions** are encoded as `<direction><direction-type><words>…</words></direction-type></direction>`, which `music21` maps to `TextExpression`. Markings that only appear as `<other-direction>`, SMuFL metadata, or **notehead**-only conventions may **not** become `TextExpression` and will be invisible to `technique_state` until supported elsewhere.
- **Free-text** is matched with normalised regex vocabulary in `technique_state.py` (language variants, not every publisher string).
- **Percussion / unpitched**: `sounding_pitch_ps_list` only returns pitches for **Note** / **Chord**, not `music21.note.Unpitched`, so cymbal lines encoded only as `<unpitched>` produce **no** timbral note events. The cymbal corpus file uses **pitched** staff notes (common in reductions) while keeping the part instrument name **Suspended Cymbal**.
- **Percussion directions** can **stack** in context (e.g. damped + beater + stroke) until explicitly overridden; interpret compound `technique_state_id` strings as cumulative state, not a single exporter token.
- **Encoding**: files are UTF-8. Prefer ASCII + common diacritics where possible; some Windows consoles mis-print accents even when parsing is correct.

## Files

| File | Intent |
|------|--------|
| `corpus_horn_techniques.musicxml` | Horn: open → stopped (gestopft) → open → cuivre |
| `corpus_horn_words_realistic.musicxml` | Same sequence with **typical** `words` layout attributes (editorial-style) |
| `corpus_strings_techniques.musicxml` | Violin: pizz → arco → sul pont → ord. → con sord. → senza sord. |
| `corpus_flute_techniques.musicxml` | Flute: ordinario → air sound → jet whistle |
| `corpus_clarinet_sax_techniques.musicxml` | Clarinet: slap tongue, multiphonic; alto sax: bisbigliando |
| `corpus_percussion_techniques.musicxml` | Suspended cymbal: let ring, damped, bow, soft mallet |
