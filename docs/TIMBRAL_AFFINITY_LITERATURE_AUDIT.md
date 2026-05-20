# Timbral affinity rules — literature audit (symbolic H_TI relief)

This document governs **notation-derived** timbral affinity rules used for optional **`H_TI_affinity_literature_relieved`**. It is **not** a claim of measured acoustic similarity, perceptual fusion, SPL, spectral analysis, or listening-test validation.

**Canonical implementation:** `src/homogeneity_analyser/taxonomy/timbral_affinity_registry.json` (machine-readable). This file is the human-readable mirror; if they diverge, **trust the JSON**.

**Default safety:** With **`timbral_affinity_relief_factor = 0.0`** (default), **`H_TI_affinity_literature_relieved` equals `H_TI_core`** — no rule fires for the headline scalar. Rules below matter only when the user enables relief and a profile that satisfies each rule’s **`profile_minimum`**.

**Evidence floors (code, not this table alone):** Rows whose **`release_status`** is **`source_key_only`** or unknown require at least the **`moderate`** affinity profile to fire; **`needs_page_verification`** requires **`exploratory`**. Only **`page_verified`** rows (none in the current registry) may fire under **`strict`** / **`conservative`**. Tier‑2 taxonomy identity on matching **`organological_family`** remains available in **`conservative`** because it is internal catalogue structure, not bibliography rows.

| rule_id | tier | similarity | profile_minimum | confidence | release_status | safe when relief > 0? | source_key(s) | APA-style reference (registry) | evidence summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| oboe_cor_anglais | 2 | 0.90 | conservative | moderate | source_key_only | yes (conservative+) | fletcher_rossing_1998_physics_of_musical_instruments | Fletcher & Rossing (1998) — see `source_registry.json` | Double-reed conical orchestral variant |
| bassoon_contrabassoon | 2 | 0.90 | conservative | moderate | source_key_only | yes | fletcher_rossing_1998_physics_of_musical_instruments | Fletcher & Rossing (1998) | Same bassoon family, register extension |
| clarinet_bass_clarinet | 2 | 0.85 | conservative | moderate | source_key_only | yes | benade_1976_fundamentals_musical_acoustics; fletcher_rossing_1998_physics_of_musical_instruments | Benade (1976); Fletcher & Rossing (1998) | Single-reed cylindrical family |
| flute_alto_flute | 2 | 0.85 | conservative | moderate | source_key_only | yes | fletcher_rossing_1998_physics_of_musical_instruments | Fletcher & Rossing (1998) | Air-jet flute family |
| flute_bass_flute | 2 | 0.82 | conservative | moderate | source_key_only | yes | fletcher_rossing_1998_physics_of_musical_instruments | Fletcher & Rossing (1998) | Air-jet family, larger bore |
| flute_piccolo | 2 | 0.75 | conservative | moderate | source_key_only | yes | fletcher_rossing_1998_physics_of_musical_instruments | Fletcher & Rossing (1998) | Same excitation; register/projection nuance |
| trumpet_cornet | 2 | 0.90 | conservative | moderate | source_key_only | yes | campbell_gilbert_myers_2021_science_of_brass_instruments | Campbell, Gilbert & Myers (2021) | Cup-mouthpiece brass cousins |
| trumpet_flugelhorn | 2 | 0.68 | conservative | moderate | source_key_only | yes | campbell_gilbert_myers_2021_science_of_brass_instruments | Campbell, Gilbert & Myers (2021) | Lip-reed; wider flare than cornet pairing |
| trombone_bass_trombone | 2 | 0.88 | conservative | moderate | source_key_only | yes | campbell_gilbert_myers_2021_science_of_brass_instruments | Campbell, Gilbert & Myers (2021) | Slide trombone family |
| euphonium_tuba | 2 | 0.72 | conservative | moderate | source_key_only | yes | campbell_gilbert_myers_2021_science_of_brass_instruments | Campbell, Gilbert & Myers (2021) | Conical low brass |
| horn_trombone_brass_cross | 3 | 0.57 | conservative | moderate | source_key_only | yes (broad brass only) | campbell_gilbert_myers_2021_science_of_brass_instruments | Campbell, Gilbert & Myers (2021) | Broad lip-reed, not identity |
| oboe_bassoon_double_reed_cross | 3 | 0.62 | conservative | moderate | source_key_only | yes | fletcher_rossing_1998_physics_of_musical_instruments | Fletcher & Rossing (1998) | Double-reed cross-subfamily |
| clarinet_saxophone_single_reed_cross | 3 | 0.60 | moderate | weak | source_key_only | only moderate+ profile | benade_1976_fundamentals_musical_acoustics | Benade (1976) | Single-reed cross-family |
| trumpet_trombone_lip_reed_cross | 3 | 0.58 | conservative | moderate | source_key_only | yes | campbell_gilbert_myers_2021_science_of_brass_instruments | Campbell, Gilbert & Myers (2021) | Lip-reed cross-subfamily |
| string_pizz_harp_plucked | 4 | 0.58 | moderate | weak | source_key_only | only moderate+; needs explicit tags | rossing_2010_science_of_string_instruments | Rossing (2010) — registry | Plucked gesture vs harp |
| col_legno_woodblock_struck_wood | 4 | 0.50 | moderate | weak | source_key_only | only moderate+; needs explicit tags | rossing_et_al_science_of_sound_pearson | Rossing et al. (Science of Sound) — registry | Struck wood / col legno gesture |
| celesta_glockenspiel_struck_pitch | 4 | 0.60 | moderate | weak | source_key_only | only moderate+ | fletcher_rossing_1998_physics_of_musical_instruments | Fletcher & Rossing (1998) | Struck pitched metal |
| cymbal_tam_tam_metallic | 4 | 0.48 | moderate | weak | source_key_only | only moderate+ | rossing_et_al_science_of_sound_pearson | Rossing et al. — registry | Large metallic decay |
| snare_bass_drum_membrane | 4 | 0.42 | moderate | weak | source_key_only | only moderate+ | rossing_et_al_science_of_sound_pearson | Rossing et al. — registry | Membrane struck |
| string_pizz_woodblock_moderate | 4 | 0.36 | moderate | weak | source_key_only | only moderate+ | rossing_et_al_science_of_sound_pearson | Rossing et al. — registry | Plucked vs woodblock |
| string_pizz_woodblock_exploratory | 4 | 0.35 | exploratory | exploratory | needs_page_verification | **no** — exploratory only | meyer_acoustics_performance_of_music | Meyer — registry | Low-confidence gesture bridge |
| sul_ponticello_metallic_perc_exploratory | 5 | 0.22 | exploratory | exploratory | needs_page_verification | **no** | rossing_2010_science_of_string_instruments | Rossing (2010) — registry | Exploratory cross-section |

**Code-only tiers (not separate JSON rows):** `timbral_affinity.py` applies tier-1 identity, tier-2 same-instrumental-subfamily defaults, and tier-3 same-excitation-class defaults with internal/taxonomy governance — see **`docs/archive_legacy/SCIENTIFIC_TECHNICAL_AUDIT.md`** (historical snapshot) for related audit notes.

**Notes**

- **Page numbers are not invented.** Where `release_status` is `source_key_only` or `needs_page_verification`, do not treat rules as page-verified evidence.
- **Strong provenance** for research claims would require `page_verified` rows keyed to consulted pages in `acoustic_profiles/source_registry.json`.
- **Exploratory** rules must not appear under **conservative** profile; **`timbral_affinity_relief_factor` default 0.0** keeps all affinity output off the headline **`H_TI_core`** path.
