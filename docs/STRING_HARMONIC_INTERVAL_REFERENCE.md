# Artificial string-harmonic interval table — source and scope

## Purpose

`homogeneity_analyser.analyzers.harmonic_pitch` maps **touching MIDI − base MIDI** (staff-notated
12-TET space) to **sounding MIDI above base** for **artificial** harmonics on **bowed orchestral strings**
only (violin, viola, cello, double bass). This drives **H_TI** register evidence when
`harmonic_pitch_policy` is `infer_common_artificial` and MusicXML supplies two chord tones with
explicit artificial harmonic markup. It is **symbolic**, **not** audio or peer-reviewed organology.

## Implemented touching intervals

| Rule id | Touching interval (semitones) | Sounding above base (semitones) | harmonic_division |
|---------|-------------------------------|----------------------------------|-------------------|
| `octave` | 12 | 12 | 2 |
| `perfect_fifth` | 7 | 19 | 3 |
| `perfect_fourth` | 5 | 24 | 4 |
| `major_third` | 4 | 28 | 5 |
| `minor_third` | 3 | 31 | 6 |

Major and minor thirds use **tempered approximations** of partial relationships; see row
`warning` / `intonation_note` in `ARTIFICIAL_STRING_HARMONIC_INTERVALS` in code.

## Source metadata (governance)

| Field | Value |
|--------|--------|
| **source_name** | Violin Harmonics — arranged by Agatha Mallett |
| **local_file** | violin_harmonics_chart.pdf |
| **local_reference_page** | 1 |
| **source_status** | practical notation chart, not peer-reviewed theoretical source |
| **release_status** | usable as practical reference; cite stronger organological sources where possible |
| **evidence_type** | string_harmonic_notation_reference |

The same interval rows are applied consistently to **viola, cello, and double bass** artificial
harmonics in code; stronger citations per instrument are encouraged for published analysis.

## Natural harmonics

When MusicXML provides **natural** harmonic with **explicit sounding** pitch, that pitch is used.
Without explicit sounding (or node) data, the analyser does **not** compute natural harmonic
pitch from noteheads alone; see `harmonic_state` / `harmonic_warning` in the event audit.

## Table location

`ARTIFICIAL_STRING_HARMONIC_INTERVALS` and `HARMONIC_INTERVAL_TABLE_SOURCE` in
`src/homogeneity_analyser/analyzers/harmonic_pitch.py`.
