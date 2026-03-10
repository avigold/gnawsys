# gnawsys

Rule-based Hebrew sentence generator for language practice. Generates grammatically correct Hebrew sentences with transliterations and English translations — no LLM at runtime.

Built to work with [Citizen Cafe](https://citizencafe.com/) vocabulary exports. When new vocab is added, a pipeline extracts, classifies, and integrates it into the generator automatically.

## How it works

The generator combines **56 sentence templates** with a vocabulary database to produce novel sentences covering:

- Present and past tense (transitive and intransitive)
- Modal constructions (want/need/can + infinitive, "feel like", "is it possible")
- 7 question types (what, where, when, why, how, how many, about what/whom)
- Negation, emphatic, frequency, temporal expressions
- Adjective predicates, possession, definite noun phrases
- Adverb patterns (still, always, sometimes, only, a lot, almost, again, together)
- Complex clauses (when, think that, sure that, because of)
- Fixed expressions and idioms

Each sentence includes:
- **Hebrew** text (right-to-left)
- **Transliteration** (romanised pronunciation)
- **English** translation

Templates are selected by weighted random choice. The generator enforces gender/number agreement between subjects, verbs, and adjectives, and handles Hebrew grammar rules like the direct object marker את.

## Requirements

- Python 3.8+ (stdlib only — for the local dev server and pipeline)
- Node.js 18+ and TypeScript (only needed if modifying the generator)

## Quick start

```bash
# Start the web server
python3 server.py

# Open in browser
open http://localhost:7749
```

The web interface displays an infinite-scrolling feed of generated sentences. Sentences are generated entirely client-side in JavaScript — scroll down to load more.

### Building from TypeScript

The client-side generator source is `generator.ts`. After making changes, recompile:

```bash
npm install      # first time only
npx tsc
```

This produces `generator.js` in place. Do not edit `generator.js` directly — it is compiled output.

## Files

| File | Description |
|---|---|
| `generator.ts` | Client-side sentence generator (TypeScript source) — 56 templates, grammar rules, helpers |
| `generator.js` | Compiled output from `generator.ts` (do not edit directly) |
| `generator.py` | Python sentence generator (used by the server API and pipeline) |
| `generator_data.json` | All vocabulary data (verbs, nouns, adjectives, etc.) in machine-editable JSON |
| `server.py` | HTTP server (port 7749) serving the web UI |
| `index.html` | Minimal frontend with infinite scroll, client-side generation |
| `tsconfig.json` | TypeScript compiler configuration |
| `pipeline.py` | Automated pipeline for integrating new vocabulary |
| `hebrew_vocab.json` | Source vocabulary export from Citizen Cafe |
| `hebrew_words.json` | Individual words extracted with transliterations |
| `hebrew_sentence_structures.json` | 47 sentence structure patterns from source material |
| `update_data.py` | Script for manually adding vocabulary to `generator_data.json` |
| `export_data.py` | One-time migration script (converts hardcoded data to JSON) |

## API

### `GET /api/sentences?n=20`

Returns `n` random sentences as JSON:

```json
[
  {
    "hebrew": "היא שותה קפה",
    "transliteration": "hi shote kafe",
    "english": "She drinks coffee"
  }
]
```

### Python

```python
from generator import generate, generate_batch

sentence = generate()
# {'hebrew': '...', 'transliteration': '...', 'english': '...'}

batch = generate_batch(20)
# list of 20 sentences
```

## Adding new vocabulary

When Citizen Cafe adds new vocab:

1. Replace `hebrew_vocab.json` with the updated export
2. Run the pipeline:

```bash
python3 pipeline.py
```

The pipeline runs 6 stages:

| Stage | What it does |
|---|---|
| **DIFF** | Compares `hebrew_vocab.json` against vocabulary already in `generator_data.json` to find new words |
| **CLASSIFY** | Classifies new words by part of speech (verb, noun, adjective, infinitive, etc.) using English translation patterns |
| **EXTRACT** | Extracts verb conjugation forms (present/past tense, gender/number) from classified words |
| **MAP** | Suggests complement categories for new verbs (what objects they pair with) |
| **MERGE** | Writes new vocabulary into `generator_data.json` |
| **VALIDATE** | Generates 2000 test sentences and checks for errors |

### Pipeline options

```bash
# Run specific stage(s)
python3 pipeline.py --stage diff --stage classify

# Preview without writing changes
python3 pipeline.py --dry-run

# Change validation sentence count
python3 pipeline.py --validate-count 5000
```

The pipeline writes findings to `pipeline_review.json` for manual review. After running, check the review file for items that need human judgment (complement type assignments, ambiguous classifications).

### Manual vocabulary additions

For targeted additions (new verbs, complements, template data), edit `update_data.py` and run it:

```bash
python3 update_data.py
```

## Vocabulary coverage

Current data:
- **9** subject pronouns (I, you m/f, he, she, we, you pl., they)
- **27** verbs with present and/or past conjugations
- **61** complements across 13 categories (food, drink, activities, people, etc.)
- **22** infinitives
- **30** adjectives (predicate, ze, midi/too, definite NP)
- **11** locations, **10** destinations, **4** countries
- **8** fixed expressions

## Architecture

```
hebrew_vocab.json ──→ pipeline.py ──→ generator_data.json
                                            │
                      ┌─────────────────────┤
                      ▼                     ▼
                generator.py          generator.ts ──→ generator.js
                      │                                     │
                      ▼                                     ▼
                server.py (/api)                 index.html (client-side)
```

The generator is purely rule-based. All randomness comes from weighted random selection of templates, subjects, verbs, and complements. Grammar agreement is enforced by filtering valid subject-verb pairs before selection. The client-side JavaScript generator is a TypeScript port of the Python original — both share the same `generator_data.json` vocabulary.
