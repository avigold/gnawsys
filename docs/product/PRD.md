# gnawsys — Product Requirements Document

## Overview

gnawsys is a Hebrew sentence practice tool that generates grammatically correct sentences with transliterations and English translations. It is designed for learners studying with [Citizen Cafe](https://citizencafe.com/) vocabulary and runs entirely as a static site on GitHub Pages — no backend required at runtime.

## Problem

Hebrew learners need high-volume, varied sentence practice to internalise grammar patterns. Existing tools either offer fixed exercises (limited variety) or rely on LLMs at runtime (expensive, unreliable, can produce incorrect Hebrew). There is no tool that combines unlimited variety with guaranteed grammatical correctness and zero runtime cost.

## Solution

A rule-based sentence generator with 56 templates covering the core grammar patterns taught in beginner-to-intermediate Hebrew courses. The generator enforces gender/number agreement, correct use of the direct object marker את, and natural complement selection. Sentences are presented in an infinite-scrolling feed with audio playback.

## Users

- Hebrew language learners (beginner to intermediate)
- Students of Citizen Cafe or similar programmes
- Self-study learners who want drilling without a tutor

## Core Features

### 1. Infinite sentence feed

An infinite-scrolling feed of Hebrew sentence cards. Each card displays:

- **Hebrew text** (right-to-left, large font)
- **Romanised transliteration** (italic, smaller)
- **English translation** (muted, smallest)
- **Grammar badges** showing which patterns are being drilled (e.g. "present, direct object", "modal + infinitive", "when clause")

Sentences are served from a curated pool of 10,000 AI-reviewed sentences in random order. Once the pool is exhausted, the generator produces fresh sentences on the fly.

### 2. Word-level hover highlighting

When the user hovers over a Hebrew word, the corresponding words in the transliteration and (when aligned) the English translation are highlighted. This helps learners connect the written Hebrew to pronunciation and meaning at the word level.

When word counts do not align between Hebrew and English (e.g. multi-word English translations), the entire English line is highlighted instead.

### 3. Audio playback

Each sentence card has a play button that speaks the Hebrew text aloud. For the curated pool of 10,000 sentences, pre-generated audio files are served (OpenAI TTS, `nova` voice, Opus format). For live-generated sentences beyond the pool, the browser's Web Speech API is used as a fallback.

A speed control on each card lets the learner cycle through playback rates: **0.5x, 0.75x, 1x, 1.25x, 1.5x**.

### 4. Client-side generation

All sentence generation runs in the browser via a JavaScript module compiled from TypeScript. The generator loads a vocabulary data file (`generator_data.json`) and produces sentences with no server calls. This enables:

- Hosting on GitHub Pages (pure static site)
- Offline capability (once assets are cached)
- Zero marginal cost per user

## Grammar Coverage

The generator covers 56 sentence templates across these categories:

| Category | Examples |
|---|---|
| Present tense | Transitive, intransitive, with time expressions |
| Past tense | Transitive, intransitive, with time expressions |
| Modal constructions | want/need/can + infinitive, "feel like", "is it possible" |
| Questions | What, where, when, why, how, how many, about what/whom |
| Negation | Present and past tense negation |
| Adjective predicates | "The coffee is hot", "This is a big city" |
| Possession | "I have", "She doesn't have" |
| Adverb patterns | still, always, sometimes, only, a lot, almost, again, together |
| Complex clauses | when, think that, sure that, because of |
| Fixed expressions | Common idiomatic phrases |
| Emphatic/frequency | "Every day", "Three times a week" |
| Definite noun phrases | Noun + adjective with ה prefix agreement |

All templates enforce:

- Subject-verb gender/number agreement
- Correct use of את before definite direct objects (ה prefix, proper names, pronouns) and its omission before indefinite objects
- Modal verbs excluded from transitive templates (want, need, start, love)
- Self-reference pronoun filtering (prevents "I don't know me")
- Plural-only subjects for "together" templates

## Vocabulary

| Category | Count |
|---|---|
| Subject pronouns | 9 (I, you m/f, he, she, we, you pl., they) |
| Verbs | 27 with present and/or past conjugations |
| Complements | 61 across 13 categories (food, drink, activities, people, etc.) |
| Infinitives | 22 |
| Adjectives | 30 (predicate, ze, midi/too, definite NP) |
| Locations | 11 |
| Destinations | 10 |
| Countries | 4 |
| Fixed expressions | 8 |

## Curated Sentence Pool

10,000 sentences are pre-validated by AI review (Claude Sonnet) against four criteria:

1. **Semantic** — Does the sentence make sense? Would a Hebrew speaker say this?
2. **Grammar** — Correct conjugation, gender/number agreement, prepositions, את usage
3. **Transliteration** — Accurate romanised pronunciation
4. **Translation** — English accurately conveys the Hebrew meaning

Sentences that fail any criterion are discarded. The curated pool is served first (in shuffled order) to ensure quality, with live generation as a fallback for infinite content.

## Audio

Pre-generated audio for all 10,000 curated sentences:

- **Model**: OpenAI TTS (`tts-1`)
- **Voice**: `nova`
- **Format**: Opus (small file size, good speech quality)
- **Total size**: ~70 MB
- **Fallback**: Web Speech API for sentences beyond the curated pool

## Architecture

```
hebrew_vocab.json ──→ pipeline.py ──→ generator_data.json
                                            │
                      ┌─────────────────────┤
                      ▼                     ▼
                generator.py          generator.ts ──→ generator.js
                      │                                     │
                      ▼                                     ▼
                server.py (/dev)             index.html (client-side)
                                                    │
                                              ┌─────┴─────┐
                                              ▼           ▼
                                     curated pool    live generation
                                     + audio files   + Web Speech API
```

### Build pipeline

| Step | Tool | Output |
|---|---|---|
| Vocabulary integration | `pipeline.py` | `generator_data.json` |
| TypeScript compilation | `npx tsc` | `generator.js` |
| Sentence curation | `review_sentences.py` (Claude API) | `curated_sentences.json` |
| Audio generation | `generate_audio.py` (OpenAI API) | `audio/*.opus` |

### Hosting

- **GitHub Pages** from the `main` branch root
- Public access, no authentication required
- All assets are static files (HTML, JS, JSON, Opus audio)

## Build Costs

One-time costs to regenerate the curated pool and audio:

| Step | Cost | Time |
|---|---|---|
| Sentence review (10K) | ~$9 | ~60 min |
| Audio generation (10K) | ~$5 | ~30 min |
| **Total** | **~$14** | **~90 min** |

## File Structure

```
gnawsys/
├── index.html                  # Frontend (single page)
├── generator.ts                # TypeScript source (sentence generator)
├── generator.js                # Compiled JS (do not edit)
├── generator.py                # Python generator (pipeline + dev server)
├── generator_data.json         # Vocabulary data
├── curated_sentences.json      # 10K AI-reviewed sentences
├── audio/                      # Pre-generated TTS audio (Opus)
│   ├── {hash}.opus             # One file per curated sentence
│   └── mapping.json            # Hash → sentence index mapping
├── server.py                   # Local dev server
├── review_sentences.py         # Sentence curation script
├── generate_audio.py           # Audio generation script
├── pipeline.py                 # Vocabulary integration pipeline
├── tsconfig.json               # TypeScript config
├── package.json                # Node dependencies
├── docs/
│   └── product/
│       └── PRD.md              # This document
└── README.md                   # Build and run instructions
```

## Future Considerations

- **Nikud (vowel diacritics)**: Add vocalised Hebrew text via Dicta Nakdan API at build time
- **Spaced repetition**: Track which grammar patterns the user struggles with and weight those more heavily
- **Filtering by grammar topic**: Let users focus on specific patterns (e.g. only past tense, only questions)
- **Mobile app wrapper**: PWA or native wrapper for offline use
- **Additional vocabulary levels**: Support for advanced Citizen Cafe levels
- **User accounts**: Save progress across devices (would require a backend)
