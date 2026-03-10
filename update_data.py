#!/usr/bin/env python3
"""Update generator_data.json with missing vocab and new template data."""
import json
import os

DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(DIR, "generator_data.json"), "r", encoding="utf-8") as f:
    D = json.load(f)

# ── NEW VERBS ──────────────────────────────────────────────────

# want (רוצה) — already used inline in templates but not in verbs list
D["verbs"].append({
    "pres": {"ms": ["רוצה", "rotse"], "fs": ["רוצה", "rotse"], "mp": ["רוצים", "rotsim"]},
    "past": {"3ms": ["רצה", "ratsa"], "1p": ["רצינו", "ratsinu"]},
    "inf": None,
    "en": ["want", "wants", "wanted", "to want", "wanting"],
    "comp": "activity",
})

# need (צריך) — very common modal
D["verbs"].append({
    "pres": {"ms": ["צריך", "tsarikh"], "fs": ["צריכה", "tsrikha"]},
    "past": {},
    "inf": None,
    "en": ["need", "needs", "needed", "to need", "needing"],
    "comp": "activity",
})

# begin/start (מתחיל)
D["verbs"].append({
    "pres": {"ms": ["מתחיל", "matkhil"], "fs": ["מתחילה", "matkhila"]},
    "past": {},
    "inf": None,
    "en": ["start", "starts", "started", "to start", "starting"],
    "comp": "activity",
})

# love (אהב) — past tense, complements like/love
D["verbs"].append({
    "pres": {},
    "past": {"1s": ["אהבתי", "ahavti"]},
    "inf": None,
    "en": ["love", "loves", "loved", "to love", "loving"],
    "comp": "food",
})

# ── EXTEND EXISTING VERBS ─────────────────────────────────────

for v in D["verbs"]:
    # Add missing 3ms past for eat
    if v["en"][0] == "eat" and "3ms" not in v["past"]:
        v["past"]["3ms"] = ["אכל", "akhal"]
    # Add missing mp present for eat
    if v["en"][0] == "eat" and "mp" not in v["pres"]:
        v["pres"]["mp"] = ["אוכלים", "okhlim"]
    # Add missing mp present for drink
    if v["en"][0] == "drink" and "mp" not in v["pres"]:
        v["pres"]["mp"] = ["שותים", "shotim"]
    # Add fs present for work
    if v["en"][0] == "work" and "fs" not in v["pres"]:
        v["pres"]["fs"] = ["עובדת", "ovedet"]
    # Add fs present for sit
    if v["en"][0] == "sit" and "fs" not in v["pres"]:
        v["pres"]["fs"] = ["יושבת", "yoshevet"]
    # Add fs present for close
    if v["en"][0] == "close" and "fs" not in v["pres"]:
        v["pres"]["fs"] = ["סוגרת", "sogeret"]
    # Add fs present for open
    if v["en"][0] == "open" and "fs" not in v["pres"]:
        v["pres"]["fs"] = ["פותחת", "potakhat"]
    # Add fs present for send
    if v["en"][0] == "send" and "fs" not in v["pres"]:
        v["pres"]["fs"] = ["שולחת", "sholakhat"]
    # Add mp present for buy
    if v["en"][0] == "buy" and "mp" not in v["pres"]:
        v["pres"]["mp"] = ["קונים", "konim"]
    # Add fs present for ask
    if v["en"][0] == "ask" and "mp" not in v["pres"]:
        v["pres"]["mp"] = ["שואלים", "sho'alim"]

# ── NEW COMPLEMENTS ────────────────────────────────────────────

# More food items
D["complements"]["food"].extend([
    ["העוגה", "ha'uga", "the cake"],
    ["ארוחת צהריים", "arukhat tsohorayim", "lunch"],
    ["סושי", "sushi", "sushi"],
])

# More buyable items
D["complements"]["buyable"].extend([
    ["העוגה", "ha'uga", "a cake"],
])

# More seeable items
D["complements"]["seeable"].extend([
    ["את החברים", "et hakhaverim", "the friends"],
    ["את המשפחה", "et hamishpakha", "the family"],
])

# More person_obj (object pronouns) — careful not to add self-referencing ones
# אותך was removed before to avoid self-reference, keep it out

# More person_et (named people with את)
D["complements"]["person_et"].extend([
    ["את השכן", "et hashakhen", "the neighbor"],
    ["את החברים", "et hakhaverim", "the friends"],
])

# More openable
D["complements"]["openable"].extend([
    ["את המקרר", "et hamekarer", "the fridge"],
    ["את הארון", "et ha'aron", "the closet"],
])

# More puttable
D["complements"]["puttable"].extend([
    ["את זה על השולחן", "et ze al hashulkhan", "it on the table"],
])

# ── NEW LOCATIONS ──────────────────────────────────────────────

D["locations"].extend([
    ["בים", "bayam", "at the beach"],
    ["בדרך", "baderekh", "on the way"],
    ["בשוק", "bashuk", "at the market"],
    ["בבנק", "babank", "at the bank"],
])

# ── NEW ADJECTIVES ─────────────────────────────────────────────

# Predicate adjectives: (m_he, m_tr, f_he, f_tr, english)
D["adjectives"]["predicate"].extend([
    ["שמח", "same'akh", "שמחה", "smekha", "happy"],
])

# ZE adjectives
D["adjectives"]["ze"].extend([
    ["טוב", "tov", "good"],
    ["נכון", "nakhon", "correct"],
])

# MIDI (too) adjectives
D["adjectives"]["midi"].extend([
    ["חם", "kham", "hot"],
    ["קר", "kar", "cold"],
])

# More definite NP pairs
D["adjectives"]["definite_np"].extend([
    ["העוגה", "ha'uga", "the cake", "הטובה", "hatova", "good"],
    ["המקרר", "hamekarer", "the fridge", "החדש", "hakhadash", "new"],
    ["השולחן", "hashulkhan", "the table", "הלבן", "halavan", "white"],
])

# ── NEW POSSESSION ─────────────────────────────────────────────

D["possession"]["possessable"].extend([
    ["חתול", "khatul", "cat"],  # check if already there
    ["כלב", "kelev", "dog"],
    ["משפחה", "mishpakha", "family"],
])
# Deduplicate possessable
seen = set()
deduped = []
for item in D["possession"]["possessable"]:
    if item[0] not in seen:
        seen.add(item[0])
        deduped.append(item)
D["possession"]["possessable"] = deduped

# More shel_nouns
D["possession"]["shel_nouns"].extend([
    ["העוגה", "ha'uga", "cake"],
    ["הכלב", "hakelev", "dog"],
])

# ── NEW TIME EXPRESSIONS ──────────────────────────────────────

# present_times: used with present tense
D["present_times"].extend([
    ["בצוהריים", "batsohorayim", "at noon"],
    ["תמיד", "tamid", "always"],
    ["לפעמים", "lif'amim", "sometimes"],
])

# past_times: used with past tense
D["past_times"].extend([
    ["בבוקר", "baboker", "in the morning"],
    ["בערב", "ba'erev", "in the evening"],
])

# ── NEW INFINITIVES ────────────────────────────────────────────

D["infinitives"].extend([
    ["לעבוד", "la'avod", "to work", "working", None],
    ["לגור", "lagur", "to live", "living", None],
    ["ללמוד", "lilmod", "to study", "studying", None],
    ["לישון", "lishon", "to sleep", "sleeping", None],
])

# ── NEW TEMPLATE DATA ─────────────────────────────────────────

TD = D["template_data"]

# Data for need_infinitive template
TD["need_inf_forms"] = {
    "ms": ["צריך", "tsarikh"],
    "fs": ["צריכה", "tsrikha"],
}

# Data for feel_like template (בא לי)
TD["feel_like_forms"] = [
    ["בא לי", "ba li", "I"],
    ["בא לך", "ba lekha", "you"],
    ["בא לו", "ba lo", "he"],
    ["בא לה", "ba la", "she"],
    ["בא לנו", "ba lanu", "we"],
    ["בא להם", "ba lahem", "they"],
]

# Data for possible template (אפשר)
TD["possible_complements"] = [
    ["לדבר", "ledaber", "to talk"],
    ["לשבת", "lashevet", "to sit"],
    ["לאכול", "le'ekhol", "to eat"],
    ["לבוא", "lavo", "to come"],
    ["לראות", "lir'ot", "to see"],
    ["לקנות", "liknot", "to buy"],
    ["לעשות", "la'asot", "to do"],
]

# Data for could_be template
TD["could_be_phrases"] = [
    ["יכול להיות", "yakhol lihyot", "Could be"],
    ["לא יכול להיות", "lo yakhol lihyot", "No way"],
]

# Data for question_about
TD["about_topics"] = [
    ["על מה", "al ma", "About what"],
    ["על מי", "al mi", "About whom"],
]

# Countable nouns for כמה questions
TD["countable_nouns"] = [
    ["חתולים", "khatulim", "cats"],
    ["חברים", "khaverim", "friends"],
    ["שיעורים", "shi'urim", "classes"],
    ["מילים", "milim", "words"],
    ["ארוחות", "arukhot", "meals"],
]

# Adverbs for new templates
TD["adverbs"] = {
    "still": ["עדיין", "adain", "still"],
    "almost": ["כמעט", "kim'at", "almost"],
    "again": ["עוד", "od", "again"],
    "together": ["יחד", "yakhad", "together"],
    "only": ["רק", "rak", "only"],
    "always": ["תמיד", "tamid", "always"],
    "sometimes": ["לפעמים", "lif'amim", "sometimes"],
    "a_lot": ["הרבה", "harbe", "a lot"],
}

# Fixed expressions
TD["fixed_expressions"] = [
    ["מה נשמע?", "ma nishma?", "What's up?"],
    ["הכל בסדר", "hakol beseder", "Everything is fine"],
    ["בהצלחה!", "behatsalkha!", "Good luck!"],
    ["לא נורא", "lo nora", "No big deal"],
    ["מה קורה?", "ma kore?", "What's happening?"],
    ["כל הכבוד!", "kol hakavod!", "Well done!"],
    ["בכיף", "bekef", "With pleasure"],
    ["סבבה", "sababa", "Cool, alright"],
]

# More even_past names
TD["even_past_names"].extend([
    ["בראד", "brad", "Brad", "m"],
])
TD["even_past_verbs_m"].extend([
    [["למד", "lamad"], "studied"],
])

# ── SAVE ───────────────────────────────────────────────────────

with open(os.path.join(DIR, "generator_data.json"), "w", encoding="utf-8") as f:
    json.dump(D, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("generator_data.json updated successfully")
