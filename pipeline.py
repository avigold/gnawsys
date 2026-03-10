#!/usr/bin/env python3
"""Pipeline: extract new vocab from hebrew_vocab.json, classify, and update generator_data.json."""
import json
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))


def load_json(name):
    with open(os.path.join(DIR, name), "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(name, data):
    with open(os.path.join(DIR, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ── STAGE 1: DIFF ──────────────────────────────────────────────

def get_generator_words(gdata):
    """Collect all Hebrew words/phrases known to the generator."""
    words = set()
    for s in gdata["subjects"]:
        words.add(s["he"])
    for v in gdata["verbs"]:
        for forms in (v["pres"], v["past"]):
            for pair in forms.values():
                words.add(pair[0])
        if v["inf"]:
            words.add(v["inf"][0])
    sv = gdata.get("study_verb", {})
    for pair in sv.get("past", {}).values():
        words.add(pair[0])
    for cat_items in gdata["complements"].values():
        for item in cat_items:
            words.add(item[0])
    for lst_name in ("locations", "destinations", "countries", "time_words",
                     "present_times", "past_times", "infinitives"):
        for item in gdata.get(lst_name, []):
            words.add(item[0])
    for adj_list in gdata["adjectives"].values():
        for item in adj_list:
            for val in item[:4] if len(item) >= 5 else item[:1]:
                if val:
                    words.add(val)
    for lst in gdata["possession"].values():
        for item in lst:
            words.add(item[0])
    td = gdata.get("template_data", {})
    for key, items in td.items():
        for item in items:
            if isinstance(item, list) and item and isinstance(item[0], str):
                words.add(item[0])
            elif isinstance(item, list) and item and isinstance(item[0], list):
                words.add(item[0][0])
    return words


def tokenize_hebrew(text):
    """Extract Hebrew word tokens from a string."""
    text = re.sub(r'[?.!,;:"\'()״׳]', ' ', text)
    return [w for w in text.split() if re.search(r'[\u0590-\u05FF]', w)]


def stage_diff(vocab, words_list, gdata):
    """Find words in vocab/words that aren't in the generator."""
    known = get_generator_words(gdata)
    words_dict = {w["hebrew"]: w for w in words_list}

    # Collect all Hebrew words from vocab sentences with their contexts
    word_contexts = {}  # hebrew_word -> list of (hebrew_sentence, english_sentence)
    for entry in vocab:
        he_content = en_content = None
        for c in entry["contents"]:
            if c["type"] == "Hebrew":
                he_content = c["content"]
            elif c["type"] == "English":
                en_content = c["content"]
        if not he_content:
            continue
        for token in tokenize_hebrew(he_content):
            if token not in known:
                if token not in word_contexts:
                    word_contexts[token] = []
                word_contexts[token].append({
                    "hebrew": he_content,
                    "english": en_content or "",
                    "lesson": entry.get("lesson", ""),
                    "level": entry.get("level", ""),
                })

    # Also check hebrew_words.json for words not in generator
    words_only_in_list = []
    for w in words_list:
        if w["hebrew"] not in known and w["hebrew"] not in word_contexts:
            words_only_in_list.append(w)

    new_words = []
    for heb, contexts in sorted(word_contexts.items()):
        entry = {"hebrew": heb, "contexts": contexts, "count": len(contexts)}
        if heb in words_dict:
            entry["transliteration"] = words_dict[heb]["transliteration"]
            entry["translation"] = words_dict[heb]["translation"]
        new_words.append(entry)

    return new_words, words_only_in_list


# ── STAGE 2: CLASSIFY ──────────────────────────────────────────

# English patterns for POS detection
_PAST_VERBS = {
    "ate", "drank", "did", "made", "talked", "worked", "sat", "closed", "opened",
    "sent", "met", "said", "thought", "asked", "lived", "flew", "went", "came",
    "bought", "traveled", "saw", "put", "wrote", "knew", "studied", "loved",
    "liked", "wanted", "needed", "could", "was", "were", "had", "got", "took",
    "gave", "told", "found", "left", "called", "tried", "used", "moved",
    "played", "ran", "read", "slept", "woke", "paid", "heard", "felt",
    "started", "finished", "arrived", "returned", "learned", "understood",
    "forgot", "remembered", "decided", "agreed", "cooked", "cleaned",
    "danced", "sang", "drove", "swam", "waited", "helped", "changed",
}

_PRESENT_STEMS = {
    "eat", "drink", "do", "make", "talk", "work", "sit", "close", "open",
    "send", "meet", "say", "think", "ask", "live", "fly", "go", "come",
    "buy", "travel", "see", "put", "write", "know", "study", "love",
    "like", "want", "need", "sleep", "wake", "pay", "hear", "feel",
    "start", "finish", "arrive", "return", "learn", "understand",
    "forget", "remember", "decide", "agree", "cook", "clean",
    "dance", "sing", "drive", "swim", "wait", "help", "run", "play",
    "read", "change", "walk", "stand",
}


def classify_word(word_entry):
    """Classify a word based on its translation pattern. Returns (pos, confidence)."""
    heb = word_entry.get("hebrew", "")
    tr = word_entry.get("translation", "")
    if not tr:
        return "unknown", "low"

    tr_lower = tr.lower().strip()

    # Infinitive: Hebrew starts with ל, translation starts with "to [verb]"
    # Must be long enough (exclude ל, לי, לך, etc.) and not "to [place]"
    if (heb.startswith("ל") and len(heb) >= 4 and tr_lower.startswith("to ")
            and not re.match(r"to (the |a |an |\w+land|atlanta|tel|where)", tr_lower)):
        to_word = tr_lower.split()[1] if len(tr_lower.split()) >= 2 else ""
        if to_word in _PRESENT_STEMS or to_word.rstrip("e") in _PRESENT_STEMS:
            return "infinitive", "high"

    # Past verb: "I/he/she/we/they [past verb]"
    past_patterns = [
        (r"^I\s+(\w+)", "past_1s"),
        (r"^he\s+(\w+)", "past_3ms"),
        (r"^she\s+(\w+)", "past_3fs"),
        (r"^we\s+(\w+)", "past_1p"),
        (r"^they\s+(\w+)", "past_3p"),
        (r"^you\s+(\w+)", "past_2s"),
    ]
    for pat, key in past_patterns:
        m = re.match(pat, tr_lower)
        if m and m.group(1) in _PAST_VERBS:
            return f"verb:{key}", "high"

    # Words with (m.)/(f.)/(m.pl.) — distinguish verbs, adjectives, numbers, nouns
    _ADJECTIVES = {
        "tired", "hungry", "busy", "sure", "ready", "happy", "sad",
        "big", "small", "new", "old", "good", "bad", "hot", "cold",
        "pretty", "beautiful", "nice", "sweet", "spicy", "hard",
        "easy", "complicated", "perfect", "amazing", "open", "closed",
        "tall", "short", "strong", "weak", "fast", "slow", "rich",
        "poor", "healthy", "sick", "clean", "dirty", "dry", "wet",
        "important", "interesting", "boring", "dangerous", "safe",
        "strange", "funny", "serious", "quiet", "loud", "young",
        "married", "single", "free", "full", "empty", "dark", "light",
        "able", "delicious", "tasty", "wonderful", "terrible",
    }
    _NUMBER_WORDS = {
        "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "first", "second", "third",
    }

    has_gender = bool(re.search(r'\([mf]\.?\s*(pl\.?)?\)', tr))
    if has_gender:
        base = re.sub(r'\s*\([^)]*\)', '', tr_lower).strip()
        base_words = set(re.split(r'[,;]\s*', base))
        base_first = base.split(",")[0].strip()

        # Check numbers first
        if base_first.rstrip("s") in _NUMBER_WORDS or base_first in _NUMBER_WORDS:
            return "number", "high"

        # Check adjectives
        if base_first in _ADJECTIVES or base_first.rstrip("s") in _ADJECTIVES:
            return "adjective", "high"

        # Check nouns (boss, student, etc. — not verbs)
        _GENDERED_NOUNS = {
            "boss", "student", "teacher", "friend", "neighbor", "doctor",
            "driver", "singer", "dancer", "cook", "actor", "writer",
            "worker", "soldier", "tourist",
        }
        if base_first.rstrip("s") in _GENDERED_NOUNS or base_first in _GENDERED_NOUNS:
            return "noun", "high"

        # Check if it's a verb by looking for verb stems
        verb_candidates = {_present_to_lemma(w) for w in base_words}
        if verb_candidates & _PRESENT_STEMS:
            if "(m.pl.)" in tr or "(m. pl.)" in tr:
                return "verb:pres_mp", "high"
            if "(m.)" in tr:
                return "verb:pres_ms", "high"
            if "(f.)" in tr:
                return "verb:pres_fs", "high"

        # Default: if single word with gender marker, likely adjective or noun
        if len(base_first.split()) == 1:
            return "noun", "medium"

    # Prepositions: starts with ב/ל/מ and translation is locational
    if heb.startswith(("ב", "ל", "מ")) and re.match(
            r"^(in|at|to|from|on|with|next to|near|inside|outside)\b", tr_lower):
        return "preposition", "high"

    # Definite noun: translation starts with "the "
    if tr_lower.startswith("the "):
        return "noun:definite", "high"

    # Question words
    if tr_lower in ("what", "where", "when", "why", "how", "who", "which",
                    "what?", "where?", "when?", "why?", "how?", "who?"):
        return "question_word", "high"

    # Conjunctions / adverbs
    if tr_lower in ("but", "or", "and", "also", "too", "still", "already",
                    "never", "always", "usually", "sometimes", "maybe",
                    "very", "really", "so", "because", "if", "that", "when",
                    "before", "after", "now", "today", "yesterday", "tomorrow"):
        return "particle", "high"

    # Numbers
    if re.match(r"^(one|two|three|four|five|six|seven|eight|nine|ten|\d+)$", tr_lower):
        return "number", "high"

    # Pronouns
    if tr_lower in ("I", "you", "he", "she", "we", "they", "it",
                    "me", "him", "her", "us", "them",
                    "my", "your", "his", "our", "their"):
        return "pronoun", "high"

    # Bare noun (default for single concrete words)
    if len(tr_lower.split()) <= 3 and not re.search(r'[.!?]', tr_lower):
        return "noun", "medium"

    # Phrase/expression
    return "expression", "low"


def stage_classify(new_words, words_list):
    """Classify new words by POS."""
    words_dict = {w["hebrew"]: w for w in words_list}
    classified = []
    for nw in new_words:
        heb = nw["hebrew"]
        word_info = words_dict.get(heb, nw)
        pos, confidence = classify_word(word_info)
        nw["pos"] = pos
        nw["confidence"] = confidence
        classified.append(nw)
    return classified


# ── STAGE 3: EXTRACT verb conjugation families ─────────────────

def stage_extract_verbs(classified, words_list):
    """Group verb forms by English lemma into conjugation families."""
    words_dict = {w["hebrew"]: w for w in words_list}
    verb_forms = {}  # english_lemma -> {key: (hebrew, translit)}

    for item in classified:
        pos = item.get("pos", "")
        if not pos.startswith("verb:"):
            continue
        heb = item["hebrew"]
        word_info = words_dict.get(heb, item)
        tr_raw = word_info.get("translation", "")
        translit = word_info.get("transliteration", "")
        conj_key = pos.split(":")[1]  # e.g., "past_1s", "pres_ms"

        # Extract English lemma from translation
        tr_lower = tr_raw.lower().strip()
        tr_clean = re.sub(r'\s*\([^)]*\)', '', tr_lower).strip()

        if conj_key.startswith("past_"):
            # "I ate" -> lemma is inferred from past tense
            parts = tr_clean.split(None, 1)
            if len(parts) >= 2:
                en_past_form = parts[-1]
                lemma = _past_to_lemma(en_past_form)
            else:
                continue
        elif conj_key.startswith("pres_"):
            # "eats (m.)" -> lemma from present
            lemma = _present_to_lemma(tr_clean)
        else:
            continue

        if not lemma:
            continue

        if lemma not in verb_forms:
            verb_forms[lemma] = {}
        verb_forms[lemma][conj_key] = (heb, translit)

    return verb_forms


_IRREGULAR_PAST_MAP = {
    "ate": "eat", "drank": "drink", "did": "do", "made": "make",
    "sat": "sit", "sent": "send", "met": "meet", "said": "say",
    "thought": "think", "flew": "fly", "went": "go", "came": "come",
    "bought": "buy", "saw": "see", "put": "put", "wrote": "write",
    "knew": "know", "was": "be", "were": "be", "had": "have",
    "got": "get", "took": "take", "gave": "give", "told": "tell",
    "found": "find", "left": "leave", "ran": "run", "read": "read",
    "slept": "sleep", "woke": "wake", "paid": "pay", "heard": "hear",
    "felt": "feel", "understood": "understand", "forgot": "forget",
    "drove": "drive", "swam": "swim", "sang": "sing", "stood": "stand",
}


def _past_to_lemma(past_form):
    """Convert English past tense to lemma."""
    if past_form in _IRREGULAR_PAST_MAP:
        return _IRREGULAR_PAST_MAP[past_form]
    if past_form.endswith("ed"):
        # worked -> work, traveled -> travel, studied -> study
        base = past_form[:-2]
        if base.endswith("i"):
            return base[:-1] + "y"
        if len(base) >= 2 and base[-1] == base[-2]:
            return base[:-1]
        return base
    if past_form.endswith("d"):
        return past_form[:-1]
    return past_form


def _present_to_lemma(present_form):
    """Convert English present tense to lemma."""
    # "eats" -> "eat", "drinks" -> "drink", "loves" -> "love"
    form = present_form.split(",")[0].strip()  # "eats, drinks" -> "eats"
    if form.endswith("ies"):
        return form[:-3] + "y"
    if form.endswith("ses") or form.endswith("zes") or form.endswith("xes") or form.endswith("ches") or form.endswith("shes"):
        return form[:-2]
    if form.endswith("ves"):
        return form[:-1]  # "loves" -> "love"
    if form.endswith("es"):
        # Check if base + "e" is a known stem (like "comes" -> "come")
        base_e = form[:-1]  # "comes" -> "come"
        base_no_e = form[:-2]  # "comes" -> "com"
        if base_e in _PRESENT_STEMS:
            return base_e
        return base_no_e
    if form.endswith("s"):
        return form[:-1]
    return form


# ── STAGE 4: MAP complement types ──────────────────────────────

def stage_map_complements(classified, gdata):
    """Suggest complement categories for new nouns based on sentence context."""
    # Words that should never be added as complements (function words, parts of compounds)
    _SKIP_WORDS = {
        "לא", "כן", "כלום", "זה", "מדי", "יותר", "גם", "עוד", "רוצה", "רוצים",
        "שהדלת", "שהחלון", "שלא", "שכן", "אבל", "או", "אז", "פעם", "הרבה",
        "בוקר", "ארוחת", "מיץ",  # parts of compound words
        "סגור", "סגורה", "פתוח", "פתוחה",  # adjectives, not objects
        "יכול", "יכולה", "צריך", "צריכה",  # modals, not objects
        "אוהב", "אוהבת", "אוהבים",  # verbs, not objects
    }
    # Also build set of words that appear inside existing compound complements
    _existing_subwords = set()
    for cat, items in gdata["complements"].items():
        for item in items:
            for part in item[0].split():
                _existing_subwords.add(part)

    suggestions = []
    existing_comp_words = {}
    for cat, items in gdata["complements"].items():
        for item in items:
            existing_comp_words[item[0]] = cat

    for item in classified:
        pos = item.get("pos", "")
        if not pos.startswith("noun"):
            continue
        if item.get("confidence") == "low":
            continue
        heb = item["hebrew"]
        if heb in existing_comp_words or heb in _SKIP_WORDS or heb in _existing_subwords:
            continue
        # Must have a real translation
        translation = item.get("translation", "")
        if not translation or len(translation) < 2:
            continue

        # Check sentence contexts for verb co-occurrence
        # The noun must appear as the OBJECT of the verb, not just anywhere in the sentence
        suggested_cats = set()
        for ctx in item.get("contexts", []):
            en_sent = ctx.get("english", "").lower()
            he_sent = ctx.get("hebrew", "")

            # Check if this word appears AFTER the verb in the Hebrew sentence
            heb_tokens = tokenize_hebrew(he_sent)
            try:
                word_idx = heb_tokens.index(heb)
            except ValueError:
                continue

            if re.search(r"\b(eat|ate|eating|eats)\b", en_sent) and word_idx > 0:
                suggested_cats.add("food")
            elif re.search(r"\b(drink|drank|drinking|drinks)\b", en_sent) and word_idx > 0:
                suggested_cats.add("drink")
            elif re.search(r"\b(buy|bought|buying|buys)\b", en_sent) and word_idx > 0:
                suggested_cats.add("buyable")
            elif re.search(r"\b(open|opened|opening|opens)\b", en_sent) and word_idx > 0:
                suggested_cats.add("openable")
            elif re.search(r"\b(close|closed|closing|closes)\b", en_sent) and word_idx > 0:
                suggested_cats.add("openable")
            elif re.search(r"\b(send|sent|sending|sends)\b", en_sent) and word_idx > 0:
                suggested_cats.add("sendable")
            elif re.search(r"\b(see|saw|seeing|sees|watch)\b", en_sent) and word_idx > 0:
                suggested_cats.add("seeable")

        if suggested_cats:
            suggestions.append({
                "hebrew": heb,
                "translation": translation,
                "transliteration": item.get("transliteration", ""),
                "suggested_categories": sorted(suggested_cats),
            })
    return suggestions


# ── STAGE 5: MERGE ─────────────────────────────────────────────

def stage_merge(gdata, verb_families, complement_suggestions, classified, words_list, dry_run=False):
    """Merge new data into generator_data.json. Returns changes log."""
    words_dict = {w["hebrew"]: w for w in words_list}
    changes = []

    # Merge new verb conjugation forms into existing verbs
    for lemma, forms in verb_families.items():
        # Find if this verb already exists in gdata
        existing_verb = None
        for v in gdata["verbs"]:
            if v["en"][0] == lemma:
                existing_verb = v
                break

        if existing_verb:
            # Add missing conjugation forms
            for conj_key, (heb, translit) in forms.items():
                if conj_key.startswith("pres_"):
                    pk = conj_key.replace("pres_", "")
                    if pk not in existing_verb["pres"]:
                        existing_verb["pres"][pk] = [heb, translit]
                        changes.append(f"ADD verb form: {lemma} pres.{pk} = {heb} ({translit})")
                elif conj_key.startswith("past_"):
                    ppk = conj_key.replace("past_", "")
                    if ppk not in existing_verb["past"]:
                        existing_verb["past"][ppk] = [heb, translit]
                        changes.append(f"ADD verb form: {lemma} past.{ppk} = {heb} ({translit})")
        else:
            # New verb entirely - build skeleton
            new_verb = {
                "pres": {},
                "past": {},
                "inf": None,
                "en": [lemma, lemma + "s", _lemma_to_past(lemma),
                       "to " + lemma, lemma + "ing"],
                "comp": "unknown",
                "_review": True,
            }
            for conj_key, (heb, translit) in forms.items():
                if conj_key.startswith("pres_"):
                    new_verb["pres"][conj_key.replace("pres_", "")] = [heb, translit]
                elif conj_key.startswith("past_"):
                    new_verb["past"][conj_key.replace("past_", "")] = [heb, translit]
            # Check if there's an infinitive in words_list
            for w in words_list:
                if w["hebrew"].startswith("ל") and lemma in w.get("translation", "").lower():
                    new_verb["inf"] = [w["hebrew"], w["transliteration"]]
                    break
            gdata["verbs"].append(new_verb)
            changes.append(f"NEW verb: {lemma} with {len(forms)} forms (NEEDS REVIEW: complement type)")

    # Merge new nouns into complement lists
    for sugg in complement_suggestions:
        heb = sugg["hebrew"]
        tr = sugg.get("transliteration", "")
        en = sugg.get("translation", "")
        for cat in sugg["suggested_categories"]:
            if cat in gdata["complements"]:
                existing = [item[0] for item in gdata["complements"][cat]]
                if heb not in existing:
                    gdata["complements"][cat].append([heb, tr, en])
                    changes.append(f"ADD complement: {heb} ({en}) -> {cat}")

    if not dry_run and changes:
        save_json("generator_data.json", gdata)

    return changes


def _lemma_to_past(lemma):
    """Simple English lemma -> past tense."""
    irregulars = {v: k for k, v in _IRREGULAR_PAST_MAP.items()}
    if lemma in irregulars:
        return irregulars[lemma]
    if lemma.endswith("e"):
        return lemma + "d"
    if lemma.endswith("y") and lemma[-2] not in "aeiou":
        return lemma[:-1] + "ied"
    return lemma + "ed"


# ── STAGE 6: VALIDATE ──────────────────────────────────────────

def stage_validate(gdata, n=2000):
    """Generate sentences and check for common errors."""
    # Reload generator with current data
    import importlib
    if "generator" in sys.modules:
        del sys.modules["generator"]
    import generator
    importlib.reload(generator)

    issues = []
    sentences = generator.generate_batch(n)

    for i, s in enumerate(sentences):
        he = s["hebrew"]
        tr = s["transliteration"]
        en = s["english"]

        # Check for empty fields
        if not he or not tr or not en:
            issues.append(f"#{i+1}: Empty field: {s}")

        # Check for double spaces
        if "  " in he or "  " in tr or "  " in en:
            issues.append(f"#{i+1}: Double space: {s}")

        # Check English capitalization
        if en and en[0].islower():
            issues.append(f"#{i+1}: Not capitalized: {en}")

        # Check for "i " (lowercase I as subject)
        if re.search(r'\bi\b', en) and "it" not in en.lower().split():
            # More precise: check for standalone lowercase 'i' that's not 'it', 'in', 'is', etc.
            words = en.split()
            for w in words:
                if w == "i":
                    issues.append(f"#{i+1}: Lowercase 'i': {en}")
                    break

        # Check Hebrew has Hebrew characters
        if not re.search(r'[\u0590-\u05FF]', he):
            issues.append(f"#{i+1}: No Hebrew chars: {he}")

        # Check for None/null in output
        if "None" in he or "None" in tr or "None" in en:
            issues.append(f"#{i+1}: Contains 'None': {s}")

    # Check data integrity
    for v in gdata["verbs"]:
        if v.get("comp") == "unknown":
            issues.append(f"VERB needs complement type: {v['en'][0]}")
        if v.get("_review"):
            issues.append(f"VERB needs review: {v['en'][0]}")

    return issues, len(sentences)


# ── MAIN ────────────────────────────────────────────────────────

def run(stages=None, dry_run=False, validate_count=2000):
    stages = stages or ["diff", "classify", "extract", "map", "merge", "validate"]

    vocab = load_json("hebrew_vocab.json")
    words_list = load_json("hebrew_words.json")
    gdata = load_json("generator_data.json")

    new_words = []
    classified = []
    verb_families = {}
    comp_suggestions = []
    changes = []

    if "diff" in stages:
        print("── STAGE 1: DIFF ──")
        new_words, words_only = stage_diff(vocab, words_list, gdata)
        print(f"  Found {len(new_words)} new words in vocab sentences")
        if words_only:
            print(f"  Found {len(words_only)} words only in hebrew_words.json (not in sentences)")
        if new_words:
            for nw in new_words[:20]:
                tr = nw.get("transliteration", "?")
                tl = nw.get("translation", "?")
                print(f"    {nw['hebrew']:15s} ({tr:15s}) = {tl:20s} [{nw['count']} occurrences]")
            if len(new_words) > 20:
                print(f"    ... and {len(new_words) - 20} more")
        else:
            print("  No new words found.")

    if "classify" in stages and new_words:
        print("\n── STAGE 2: CLASSIFY ──")
        classified = stage_classify(new_words, words_list)
        by_pos = {}
        for c in classified:
            pos = c["pos"]
            by_pos.setdefault(pos, []).append(c)
        for pos, items in sorted(by_pos.items()):
            print(f"  {pos}: {len(items)}")
            for item in items[:5]:
                conf = item['confidence']
                tr = item.get('translation', '?')
                print(f"    {item['hebrew']:15s} = {tr:25s} [{conf}]")
            if len(items) > 5:
                print(f"    ... and {len(items) - 5} more")

    if "extract" in stages and classified:
        print("\n── STAGE 3: EXTRACT VERBS ──")
        verb_families = stage_extract_verbs(classified, words_list)
        if verb_families:
            for lemma, forms in sorted(verb_families.items()):
                print(f"  {lemma}:")
                for key, (heb, tr) in sorted(forms.items()):
                    print(f"    {key:10s} = {heb} ({tr})")
        else:
            print("  No verb families extracted.")

    if "map" in stages and classified:
        print("\n── STAGE 4: MAP COMPLEMENTS ──")
        comp_suggestions = stage_map_complements(classified, gdata)
        if comp_suggestions:
            for s in comp_suggestions:
                print(f"  {s['hebrew']:15s} ({s['translation']}) -> {', '.join(s['suggested_categories'])}")
        else:
            print("  No complement suggestions.")

    if "merge" in stages:
        print("\n── STAGE 5: MERGE ──")
        changes = stage_merge(gdata, verb_families, comp_suggestions, classified, words_list, dry_run=dry_run)
        if changes:
            for c in changes:
                prefix = "[DRY RUN] " if dry_run else ""
                print(f"  {prefix}{c}")
        else:
            print("  No changes to merge.")

    if "validate" in stages:
        print(f"\n── STAGE 6: VALIDATE ({validate_count} sentences) ──")
        issues, total = stage_validate(gdata, validate_count)
        if issues:
            print(f"  {len(issues)} issues found in {total} sentences:")
            for issue in issues[:30]:
                print(f"    {issue}")
            if len(issues) > 30:
                print(f"    ... and {len(issues) - 30} more")
        else:
            print(f"  All {total} sentences OK.")

    # Write review file
    review = {
        "new_words": len(new_words),
        "classified": len(classified),
        "verb_families": len(verb_families),
        "complement_suggestions": len(comp_suggestions),
        "changes": changes,
        "words": [
            {
                "hebrew": c["hebrew"],
                "transliteration": c.get("transliteration", ""),
                "translation": c.get("translation", ""),
                "pos": c.get("pos", ""),
                "confidence": c.get("confidence", ""),
                "contexts": c.get("contexts", [])[:3],
            }
            for c in classified
        ],
    }
    save_json("pipeline_review.json", review)
    print(f"\n  Review file written to pipeline_review.json")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hebrew vocab pipeline")
    parser.add_argument("--stage", choices=["diff", "classify", "extract", "map", "merge", "validate"],
                        action="append", help="Run specific stage(s)")
    parser.add_argument("--dry-run", action="store_true", help="Don't write changes")
    parser.add_argument("--validate-count", type=int, default=2000, help="Number of sentences to validate")
    args = parser.parse_args()

    run(stages=args.stage, dry_run=args.dry_run, validate_count=args.validate_count)
