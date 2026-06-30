# Instrumental articulation catalogue

Single reference for **canonical instruments**, **taxonomy families / macrofamilies**, **playing-state dimensions** (`TechniqueState`), **direction and articulation parsing** (notation-derived), and **legacy matrix technique labels** used across the Timbral Instrumental Homogeneity codebase.

**Scope:** MusicXML / music21 symbolic pipeline only — **not** measured audio, **not** PDF semantics.

**Authoritative sources:** `src/homogeneity_analyser/taxonomy/instrument_taxonomy.py`, `analyzers/hti_taxonomy.py`, `analyzers/technique_state.py`, `analyzers/*_technique.py`, `TECHNICAL_MANUAL.md` Appendix D, `docs/QUICK_REFERENCE_SYMBOLIC_NAMES.md`, and the **H_timbral** design notes listed in **Part D** (plus `docs/ARCHITECTURE.md`, `docs/HOMOGENEITY_ANALYSER_MASTER_DOCUMENT.md`).

---

## Part A — Instrument taxonomy

### A.1 Instrumental subfamilies (`family` on events)

| Python constant | `family` string |
|-----------------|----------------|
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

Unmatched part names resolve to a **normalised slug** as canonical instrument and `family` = `other`.

### A.2 Macrofamilies (`macrofamily_uniformity`, `hti_taxonomy.py`)

| `macrofamily` | Subfamilies grouped |
|---------------|---------------------|
| `strings` | `strings` |
| `woodwinds` | `flutes`, `recorders`, `oboes`, `clarinets`, `bassoons`, `saxophones` |
| `brass` | `brass` |
| `percussion` | `percussion` |
| `keyboards` | `keyboard` |
| `voice` | `voice` |
| `other` | `other`, unknown, empty |

### A.3 String-section desk labels

`match_string_section_desk_label` recognises score-style desk lines (e.g. violin/viola/cello/double bass + Roman numeral + stand numbers) and fills `section_label` / `desk_group` in orchestration audit fields. See `instrument_taxonomy.py` and Appendix D.4.

### A.4 Canonical instruments and aliases (`_CANONICAL_INSTRUMENTS`)

**Espelho do código / code mirror:** cada alias na lista abaixo vem **unicamente** do dicionário `_CANONICAL_INSTRUMENTS` em `src/homogeneity_analyser/taxonomy/instrument_taxonomy.py`. Este Markdown **não** acrescenta abreviaturas, traduções nem variantes que não existam já nesse ficheiro. Para novos reconhecimentos de partitura, edite as tuplas `aliases` em Python (e mantenha `get_alias_collision_log()` vazio).

Each row: **canonical name** (stored on timbral events after resolution) and **aliases** matched from part names (longest-key wins; short tokens such as `fl` only in short phrases).

#### `bassoons`

- **bassoon** — bassoon; fagott; bn.; bsn.; fg.; fg; fag.; fagote
- **contrabassoon** — contrabassoon; contrabassoon in f; cfg.; cbn; contrafagote; contra fagote; contra fagotto; contrafagotto
- **crumhorn** — crumhorn
- **dulcian** — dulcian; dulciana
- **racket** — racket

#### `brass`

- **alphorn** — alphorn
- **alto trombone** — alto trombone; trombone alto
- **bass trombone** — bass trombone; trombone baixo
- **bass trumpet** — bass trumpet; trompete baixo
- **bugle** — bugle
- **cimbasso** — cimbasso
- **contrabass trombone** — contrabass trombone; trombone contrabaixo
- **cornet** — cornet; cornetto; corneta; cornetim
- **cornett** — cornett
- **didgeridoo** — didgeridoo
- **euphonium** — baritone horn; euphonium; eufónio; eufonio; bombardino
- **flugelhorn** — flugelhorn; fliscorne
- **horn** — french horn; horn; hn.; hn; trompa; trompa em fa
- **mellophone** — mellophone
- **natural horn** — cor de chasse; hunting horn; natural horn; trompa natural
- **ophicleide** — ophicleide
- **piccolo trumpet** — piccolo trumpet; trompete piccolo
- **serpent** — serpent
- **sousaphone** — sousaphone
- **trombone** — tenor trombone; soprano trombone; sackbut; trombone; trb.; tbn.
- **trumpet** — natural trumpet; trumpet; tpt.; trp.; tr.; tr; trompete; trompete em do
- **tuba** — bass tuba; tuba; tba.
- **wagner tuba** — wagner tuba; tuba wagneriana

#### `clarinets`

- **a clarinet** — clarinet in a; a clarinet; cl in a; clarinete em lá; clarinete em la
- **alto clarinet** — alto clarinet
- **b flat clarinet** — clarinet in b flat; clarinet in bb; b flat clarinet; bb clarinet; cl in bb; clarinete em si bemol; clarinete em sib
- **bass clarinet** — bass clarinet; bass cl.; bcl; clarinete baixo
- **basset clarinet** — basset clarinet
- **basset horn** — basset horn
- **c clarinet** — clarinet in c; c clarinet
- **clarinet** — soprano clarinet; clarinet; clarinete; cl.; cl
- **contrabass clarinet** — contrabass clarinet; cbcl; clarinete contrabaixo
- **e flat clarinet** — clarinet in e flat; clarinet in eb; e flat clarinet; eb clarinet; cl in eb; clarinete em mi bemol; requinta

#### `flutes`

- **alto flute** — alto flute; flauta alto; flauta em sol
- **bansuri** — bansuri
- **bass flute** — bass flute; flauta baixo
- **dizi** — dizi
- **fife** — fife
- **flute** — flute; traverso; fl.; fl; flauta; flauta transversal
- **ocarina** — ocarina
- **pan flute** — pan flute; pan pipes
- **piccolo** — piccolo; picc.; picc; flautim; ottavino
- **shakuhachi** — shakuhachi
- **tin whistle** — tin whistle

#### `keyboard`

- **accordion** — accordion; acordeão
- **bandoneon** — bandoneon
- **celesta** — celesta; celeste; cel.
- **clavichord** — clavichord
- **clavinet** — clavinet
- **concertina** — concertina
- **fortepiano** — fortepiano
- **harmonica** — harmonica
- **harmonium** — harmonium
- **harpsichord** — harpsichord; cravo
- **organ** — organ; pipe organ; org.; órgão; orgao
- **piano** — grand piano; upright piano; electric piano; piano; pf.; pno.
- **spinet** — spinet
- **synthesizer** — synthesizer; synth; sintetizador; synth.
- **virginal** — virginal

#### `oboes`

- **bass oboe** — bass oboe
- **cor anglais** — cor anglais; english horn; cor inglês; cor ingles; corno inglese
- **duduk** — duduk
- **heckelphone** — heckelphone; heckelfone
- **musette** — musette
- **oboe** — oboe; ob.; ob; oboé
- **oboe d'amore** — oboe d'amore; oboé d'amore; oboe de amor; oboe d amore; oboe damore
- **oboe da caccia** — oboe da caccia
- **shawm** — shawm
- **suona** — suona

#### `percussion`

- **bass drum** — bass drum; bd; bombo
- **bongos** — bongos; bongo
- **cajón** — cajón; cajon
- **castanets** — castanets
- **claves** — claves
- **congas** — congas; conga
- **cowbell** — cowbell
- **crotales** — crotales
- **cymbal** — cymbal; cymbals; pratos
- **djembe** — djembe
- **glockenspiel** — glockenspiel; orchestral bells; glock.
- **gong** — gong
- **marimba** — marimba
- **percussion** — percussion; drums; drum set; drum kit; perc.; percussão; percussao
- **rototom** — rototom
- **snare drum** — snare drum; sd; caixa clara; tarola
- **steelpan** — steelpan; steel drum
- **suspended cymbal** — suspended cymbal; prato suspenso
- **tabla** — tabla
- **tam-tam** — tam-tam; tamtam
- **tambourine** — tambourine
- **temple block** — temple block
- **timpani** — timpani; kettledrum; timp.; tímpanos; timpanos
- **tom-tom** — tom-tom; tom tom
- **triangle** — triangle; tgl; triângulo
- **tubular bells** — tubular bells; chimes
- **vibraphone** — vibraphone; vibes; vib.; vibrafone
- **wind chimes** — wind chimes
- **wood block** — wood block
- **xylophone** — xylophone; xyl.; xilofone

#### `recorders`

- **alto recorder** — alto recorder
- **bass recorder** — bass recorder
- **recorder** — recorder; blockflöte; block flute
- **sopranino recorder** — sopranino recorder
- **soprano recorder** — soprano recorder
- **tenor recorder** — tenor recorder

#### `saxophones`

- **alto saxophone** — alto saxophone; alto sax; saxofone alto
- **baritone saxophone** — baritone saxophone; baritone sax; saxofone baritono
- **bass saxophone** — bass saxophone
- **saxophone** — saxophone; sax
- **sopranino saxophone** — sopranino saxophone
- **soprano saxophone** — soprano saxophone
- **tenor saxophone** — tenor saxophone; tenor sax; saxofone tenor

#### `strings`

- **banjo** — banjo
- **baryton** — baryton
- **bass guitar** — bass guitar
- **cello** — violoncello; violoncelo; violoncélo; cello; vc.; vlc.
- **cittern** — cittern
- **double bass** — double bass; contrabass; cb.; cb; db.; contrabaixo; bass
- **dulcimer** — dulcimer
- **erhu** — erhu
- **guitar** — acoustic guitar; electric guitar; classical guitar; guitar; guitarra
- **guzheng** — guzheng
- **harp** — harp; hp.; harpa
- **koto** — koto
- **lute** — lute
- **mandola** — mandola
- **mandolin** — mandolin
- **pipa** — pipa
- **shamisen** — shamisen
- **sitar** — sitar
- **theorbo** — theorbo
- **ukulele** — ukulele
- **vihuela** — vihuela
- **viol** — viol
- **viola** — viola; vla.; va.; viola de arco
- **viola da gamba** — viola da gamba
- **violin** — violin; vln.; vn.; vl.; violino; violino i; violino ii; first violins; second violins
- **zither** — zither

#### `voice`

- **alto** — alto
- **baritone** — baritone
- **bass** — bass voice
- **choir** — choir; chorus
- **contralto** — contralto
- **countertenor** — countertenor
- **mezzo-soprano** — mezzo-soprano; mezzo soprano
- **soprano** — soprano
- **tenor** — tenor
- **voice** — voice; vocals

---

## Part B — Technique state model (`TechniqueState`, `technique_state.py`)

Persistent playing state while scanning a part in chronological order; merged with **note-local articulations** and **TextExpression / Dynamic** directions.

### B.1 Dataclass fields (all families)

| Field | Role |
|-------|------|
| `family` | Instrumental subfamily |
| `instrument` | Canonical instrument id |
| `primary` | Brass hand-stopping / mutes lane; wind "lane"; often `ordinary` |
| `mute` | Brass mutes; string con sord |
| `contact_point` | Bowed-string bridge / fingerboard contact |
| `excitation` | Bowed-string pizz / arco / col legno / tremolo lane |
| `articulation_effect` | e.g. brass flutter-tongue; bowed tremolo flag |
| `resonance` | Percussion let ring / damped / choke |
| `noise_component` | Reserved / ordinary |
| `pressure` | e.g. molto flautando, overpressure, scratch tone |
| `beater` | Percussion mallet / stick / hands |
| `stroke` | Percussion roll, rim, edge, scrape, bowed |
| `special` | Tuple; string harmonics `harmonic:*`, pressure `pressure:*` |

### B.2 Composite `technique_state_id` (examples)

- **Brass:** `horn|open`, `horn|stopped`, `trumpet|harmon_mute|stem_out`, `horn|cuivre`, …
- **Bowed strings:** `violin|arco`, `violin|arco|sul_pont`, `cello|pizz`, …
- **Winds:** `clarinet|flutter`, `flute|bisbigliando`, …
- **Percussion:** `suspended cymbal|let_ring`, `snare drum|brushes`, …

### B.3 `technique_uniformity_key` (instrument-free)

- Default bucket for unmarked technique concentration: **`ordinary_default`** (`ORDINARY_DEFAULT_UNIFORMITY_KEY`).
- Derived from the tail of `technique_state_id` after dropping the instrument prefix; tail tokens normalised (`sul_pont` → `sul_ponticello`, `pizz` → `pizzicato`, …).

### B.4 Brass — internal tokens (`primary`, `mute`, `articulation_effect`)

| Token | Meaning (summary) |
|-------|-------------------|
| open / ordinary | Open / ordinary playing |
| stopped | Hand-stopped / closed (+ sign, bouché, gestopft, …) |
| half_stopped | Half stopped / half muted |
| cuivre | Brassy / metallic / bells up |
| none (mute) | No mute |
| straight_mute | Straight mute |
| cup_mute | Cup mute |
| harmon_mute, harmon_stem_in, harmon_stem_out | Harmon / wah-wah mute stem position |
| bucket_mute | Bucket mute |
| plunger | Plunger / derby / hat |
| practice_mute | Practice mute |
| muted_generic | Generic con sord / muted |
| flutter | `articulation_effect` flutter-tongue |

**Direction text** (multilingual) is parsed in `_apply_brass_direction`: open/stopped/cuivre/mutes/growl/shake/lip trill/glissando/fall/doit/rip/smear/breath attack/air tone, etc.

### B.5 Bowed strings (violin, viola, cello, double bass)

| Dimension | Typical non-default values |
|-----------|------------------------------|
| `excitation` | `arco`, `pizz`, `snap_pizz`, `col_legno_battuto`, `col_legno_tratto`; sul-g / sul-d style tokens from text |
| `mute` | `none`, `muted` (con sord) |
| `contact_point` | `sul_pont`, `molto_sul_pont`, `sul_tasto`, `molto_sul_tasto`, `behind_bridge`, `on_bridge`, `sub_ponticello` |
| `pressure` | `molto_flautando`, `overpressure`, `scratch_tone` |
| `articulation_effect` | `tremolo` (from tremolo expression) |
| `special` | `harmonic:natural_harmonic`, `harmonic:artificial_harmonic`, `harmonic:harmonic_generic`, `pressure:…` |

**music21 merges:** `Pizzicato`, `NailPizzicato`, `SnapPizzicato`, `FrettedPluck`, `StringHarmonic`, `Harmonic`, `Stopped` (mute), `Tremolo` expression; diamond notehead → harmonic hint.

### B.6 Woodwinds (flutes, oboes, clarinets, bassoons, saxophones)

Wind **lane** stored in `primary`: `ordinario`, `bisbigliando`, `tongue_ram`, `jet_whistle`, `whistle_tone`, `harmonic`, `flutter`, `slap`, `key_click`, `multiphonic`, `air_sound`, `growl`, `subtone`, `singing_and_playing`, `vibrato`, …

### B.7 Percussion

| Dimension | Values (from `_apply_percussion_direction`) |
|-----------|--------------------------------------------------|
| `beater` | `hard_mallet`, `yarn_mallet`, `felt_mallet`, `soft_mallet`, `rubber_mallet`, `wood_stick`, `metal_stick`, `brushes`, `hands`, `fingers`, `superball`, `bow`, … |
| `resonance` | `open`, `let_ring`, `damped`, `choke` |
| `stroke` | `ordinary`, `bowed`, `roll`, `rimshot`, `rim`, `edge`, `center`, `scrape` |

### B.8 Ordinal dynamic marks (not SPL)

Parsed by `parse_standard_dynamic_mark` from single-token text after normalisation (exact token match). **Not** SPL or measured loudness.

`pppp`, `ppp`, `pp`, `mpp`, `mp`, `mf`, `mfp`, `nf`, `f`, `ff`, `fff`, `ffff`, `fp`, `sf`, `sfp`, `sfz`, `sffz`, `fz`, `rf`, `sp`, `sfzp`, `n`, `p`.

### B.9 Where notation is read from

- `iter_timbral_elements`: `TextExpression`, `RehearsalMark`, `Dynamic`, `Crescendo`/`Diminuendo`, then `Note`/`Chord`/`Unpitched` in offset order.
- `notation_text_context_for_note` for keyword context (timbral defaults differ by caller).

---

## Part C — Legacy discrete technique labels (`*_technique.py`)

Coarse labels for **pairwise timbral matrices** where full `TechniqueState` is not used.

| Module | Labels |
|--------|--------|
| `brass_technique.py` | open, straight_mute, cup_mute, harmon_mute, bucket_mute, stopped, half_stopped, cuivre, flutter, muted_generic, unknown |
| `string_technique.py` | arco, tremolo, sul_pont, sul_tasto, harmonic, muted, pizz, unknown |
| `flute_technique.py` | ordinario, vibrato, breathy, flutter, harmonic, whistle, air_keys, unknown |
| `clarinet_technique.py` | ordinario, light_vibrato, flutter, breathy, slap, multiphonic, unknown |
| `double_reed_technique.py` | ordinario, flutter, multiphonic, breathy, unknown |
| `saxophone_technique.py` | ordinario, subtone, growl, flutter, slap, breathy, overtone_special, unknown |
| `percussion_technique.py` | ordinario, mallet_hard, mallet_soft, mallet_felt, mallet_yarn, sticks, brushes, snare_on, snare_off, damped, open, rolled, bowed, vibraphone_pedal, vibraphone_no_pedal, cymbal_suspended, cymbal_crash, rim_stroke, unknown |

---

## Part D — Documentation map and H_timbral symbolic layer

These notes are **notation-derived orchestration similarity** (shared timbral event pipeline with **H_TI_core**), **not** acoustic measurement. Full prose stays in each linked file; this section is a **checklist** so nothing material is missing from the one-stop catalogue.

| Document | Role (summary) | Primary code |
|----------|----------------|--------------|
| `docs/QUICK_REFERENCE_SYMBOLIC_NAMES.md` | Compact index of families, canonicals, `TechniqueState`, legacy labels | same as Parts A–C |
| `docs/ARCHITECTURE.md` | Repo map; lists all `H_TIMBRAL_*.md` paths next to `analyzers/` | — |
| `docs/HOMOGENEITY_ANALYSER_MASTER_DOCUMENT.md` | Product-level overview; table mapping family → design doc | `analyzers/timbral.py`, `hti.py` |
| `docs/H_TIMBRAL_SCORE_REPRESENTATION.md` | Sounding pitch for tessitura; technique text context; unpitched percussion vs register | `timbral_sounding_pitch.py`, `notation_context.py`; **H_TI** **`register_compactness`** uses `hti.compute_register_compactness_fields` (**pitch-space** span + pairwise **semitone-distance** — **not** the optional **interval-class** table in `symbolic_blend_layers.py`) |
| `docs/H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md` | Small **cross-family** boosts (`timbre_cross_relations`); evidence tags | `timbre_cross_relations.py`, `timbral.py` |
| `docs/H_TIMBRAL_STRINGS.md` | String pairwise refinement | `string_pairwise_timbral.py` |
| `docs/H_TIMBRAL_BRASS.md` | Brass buckets, tessitura, technique matrix | `brass_pairwise_timbral.py`, `brass_technique.py` |
| `docs/H_TIMBRAL_FLUTES.md` | Flute subtype + tessitura + technique | `flute_pairwise_timbral.py`, `flute_technique.py` |
| `docs/H_TIMBRAL_CLARINETS.md` | Clarinet subtype zones (chalumeau/clarion/altissimo), technique | `clarinet_pairwise_timbral.py`, `clarinet_technique.py` |
| `docs/H_TIMBRAL_DOUBLE_REEDS.md` | Oboes vs bassoons macro-cluster matrix | `double_reed_pairwise_timbral.py`, `double_reed_technique.py` |
| `docs/H_TIMBRAL_SAXOPHONES.md` | Sax size line + four tessitura zones | `saxophone_pairwise_timbral.py`, `saxophone_technique.py` |
| `docs/H_TIMBRAL_PERCUSSION.md` | `PercussionMeta` ontology + pairwise factors | `percussion_ontology.py`, `percussion_pairwise_timbral.py`, `percussion_technique.py` |

### D.1 Score representation (`H_TIMBRAL_SCORE_REPRESENTATION.md`)

- **Sounding (concert) MIDI** for timbral events: `timbral_sounding_pitch.sounding_pitch_ps_list` uses `note.getInstrument()` when present, else part `Instrument.transposition` (Bb clarinet, F horn, Eb alto sax, …). Applied on the timbral path only.
- **Technique text:** `notation_text_context_for_note` — `measure_text="prior"` vs `"legacy"` vs `"none"`; timbral timeline uses `iter_timbral_elements` + `apply_persistent_text` for persistent directions; note-local text merged into a **copy** of the timeline per note so it does not leak to following notes.
- **Percussion / register:** unpitched canonicals omit melodic span; percussion-dominated unpitched windows blend register toward `unpitched_percussion_register_proxy` via `percussion_pairwise_timbral`. Pitched percussion keeps concert span.

### D.2 Verified cross-relations (`H_TIMBRAL_VERIFIED_CROSS_RELATIONS.md`)

Evidence tags: `directly_attested`, `bibliographically_derived`, `conditional`, `unconditional`. All boosts globally capped.

| ID | Relation (canonical instruments / scope) | Notes |
|----|--------------------------------------------|-------|
| A | Double-reed macro-cluster (oboe family ↔ bassoon family) | No extra boost here — affinity in `double_reed_pairwise_timbral.py` to avoid double count |
| B | `tenor saxophone` ↔ clarinet (narrow) | Conditional tessitura; excludes bass/contrabass/alto clarinet |
| C | `alto saxophone` ↔ `horn` | Conditional tessitura |
| D | `trumpet` ↔ `oboe` (not cor anglais / musette) | Conditional; small additive bump |
| E | `natural horn` ↔ `trumpet` / `bass trumpet` | **Implemented**; valve `horn` excluded |
| F | `bass clarinet` ↔ `bassoon` | Bibliographically derived, unconditional (overlap-weighted) |
| G | `horn` ↔ `bassoon` | Bibliographically derived, unconditional |
| H | High-register soprano clarinets ↔ flute | Only `clarinet`, `b flat clarinet`, `a clarinet`, `c clarinet`; conditional MIDI bands |
| I | Oboe ↔ bassoon vs oboe ↔ flute/clarinet | Ordering from double-reed subsystem + tests |

### D.3 Family refinement summaries (`H_TIMBRAL_*.md`)

**Strings — `H_TIMBRAL_STRINGS.md`:** Bowed orchestral **violin / viola / cello / double bass** only; blend formula ``f·H_pair + (1-f)·legacy``; section matrix, register decay τ, legacy vs multi-state technique paths. Authoritative code: **`string_pairwise_timbral.py`** (prose in the Markdown file should stay aligned with it).

**Brass — `H_TIMBRAL_BRASS.md`:** After strings, brass mass blends toward brass pairwise score. **Section buckets:** trumpet-like, horn-like, trombone, bass trombone, tuba-like (see doc). **`bass trombone`** canonical distinct from **`trombone`**. Tessitura: quartile zones per bucket + normalized height. Technique: `brass_technique_from_note` + matrix.

**Flutes — `H_TIMBRAL_FLUTES.md`:** Blend after strings+brass. Subtypes: flute, alto flute, bass flute, piccolo vs **other** bucket (fife, shakuhachi, …). `_SUBTYPE_SIM` encodes intra-family distances; tessitura like brass quartiles; `flute_technique_from_note`.

**Clarinets — `H_TIMBRAL_CLARINETS.md`:** Blend after flutes. Canonical subtypes listed in doc; **`_normalize`** hyphen handling. Register bands: **chalumeau** `< 66`, **clarion** `66–79`, **altissimo** `≥ 80` MIDI for soprano-family; lower clarinets use `_CLAR_TESS_BOUNDS`. `clarinet_technique_from_note`.

**Double reeds — `H_TIMBRAL_DOUBLE_REEDS.md`:** Taxonomy keeps `oboes` vs `bassoons`; pairwise adds **double-reed macro-cluster** matrix (`_SUBTYPE_SIM`). Technique: `double_reed_technique_from_note`.

**Saxophones — `H_TIMBRAL_SAXOPHONES.md`:** After double-reeds. Subtypes sopranino → bass + generic `saxophone` bucket; four tessitura zones; `saxophone_technique_from_note`.

**Percussion — `H_TIMBRAL_PERCUSSION.md`:** `percussion_ontology.PercussionMeta`: `macro_class`, `material`, `pitch_status`, resonance/noise ordinals, `size_bin` (1–5) for unpitched pairing, `tessitura_lo/hi` when pitched. Pairwise score combines instrument / pitch_status / technique / register-size / resonance / noise (see doc). Generic `percussion` → low-confidence meta.

### D.4 Where this catalogue fits

- **Parts A–C** = instruments + articulation **tokens** and parsers.  
- **Part D** = **how those events feed H_timbral refinements** and **cross-family** policy.  
- **`TECHNICAL_MANUAL.md` Appendix D** = CSV column names, pitch modes, harmonic policies not duplicated here.

---

## Part E — Maintenance

1. When adding instruments: extend `_CANONICAL_INSTRUMENTS` in `instrument_taxonomy.py`, then refresh **this file**, **`TECHNICAL_MANUAL.md` Appendix D**, and **`docs/QUICK_REFERENCE_SYMBOLIC_NAMES.md`**.
2. When adding technique tokens: extend `TechniqueStateContext` / `_apply_*_direction` / `merge_note_technique_state`, then document new tokens here and in Appendix D if user-visible.
3. When changing timbral pairwise or cross-relation behaviour: update the relevant **`docs/H_TIMBRAL_*.md`** file and the **Part D** summary rows in **this catalogue**.
4. When changing **`string_pairwise_timbral.py`** or string constants in **`default_profiles.json`**, update **`docs/H_TIMBRAL_STRINGS.md`** and the strings bullet in **Part D.3** of **this catalogue**.
