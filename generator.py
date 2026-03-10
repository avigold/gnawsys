"""Rule-based Hebrew sentence generator."""
import json
import os
import random

# === LOAD DATA ===
_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_dir, "generator_data.json"), "r", encoding="utf-8") as _f:
    _DATA = json.load(_f)

SUBJECTS = _DATA["subjects"]
VERBS = _DATA["verbs"]
STUDY_VERB = _DATA["study_verb"]

_comp = _DATA["complements"]
FOOD = _comp["food"]
DRINK = _comp["drink"]
OPENABLE = _comp["openable"]
SENDABLE = _comp["sendable"]
ACTIVITY = _comp["activity"]
PERSON_OBJ = _comp["person_obj"]
PERSON_ET = _comp["person_et"]
BUYABLE = _comp["buyable"]
SEEABLE = _comp["seeable"]
WRITABLE = _comp["writable"]
PUTTABLE = _comp["puttable"]
QUOTE = _comp["quote"]
ABOUT_IT = _comp["about_it"]

COMP_MAP = {
    "food": FOOD, "drink": DRINK, "openable": OPENABLE, "sendable": SENDABLE,
    "activity": ACTIVITY, "person": PERSON_ET, "person_obj": PERSON_OBJ,
    "buyable": BUYABLE, "seeable": SEEABLE, "writable": WRITABLE, "puttable": PUTTABLE,
    "quote": QUOTE, "about_it": ABOUT_IT, "about": ABOUT_IT,
}

LOCATIONS = _DATA["locations"]
DESTINATIONS = _DATA["destinations"]
COUNTRIES = _DATA["countries"]
TIME_WORDS = _DATA["time_words"]
PRESENT_TIMES = _DATA["present_times"]
PAST_TIMES = _DATA["past_times"]

_adj = _DATA["adjectives"]
PRED_ADJ = _adj["predicate"]
ZE_ADJ = _adj["ze"]
MIDI_ADJ = _adj["midi"]
DEF_NP = _adj["definite_np"]

_poss = _DATA["possession"]
POSSESSABLE = _poss["possessable"]
YESH_L = _poss["yesh_l"]
POSS_MOD = _poss["modifiers"]
SHEL = _poss["shel"]
SHEL_NOUNS = _poss["shel_nouns"]

INFINITIVES = _DATA["infinitives"]

_TD = _DATA["template_data"]
_EVEN_NAMES = _TD["even_past_names"]
_EVEN_VERBS_M = _TD["even_past_verbs_m"]
_EVEN_VERBS_F = _TD["even_past_verbs_f"]
_SURE_CLAUSES = _TD["sure_that_clauses"]
_BECAUSE_CAUSES = _TD["because_of_causes"]
_BECAUSE_STATES = _TD["because_of_states"]
_NOBODY_OPENERS = _TD["nobody_openers"]
_FREQ_COUNTS = _TD["frequency_counts"]
_FREQ_PERIODS = _TD["frequency_periods"]

# Modal verbs that should only be used with infinitives, not as regular transitive verbs
_MODAL_VERBS = {"want", "need", "start", "love"}

# === HELPERS ===

def pick(lst):
    return random.choice(lst)

def get_comp(verb, subj=None):
    ct = verb.get("comp")
    if ct == "time_or_loc":
        return pick(LOCATIONS + PRESENT_TIMES)
    if ct == "location":
        return pick(LOCATIONS)
    if ct == "destination":
        return pick(DESTINATIONS)
    if ct == "country":
        return pick(COUNTRIES)
    if ct in COMP_MAP:
        pool = COMP_MAP[ct]
        # Filter out self-referencing pronouns
        if ct == "person_obj" and subj:
            pronoun_map = {"I": "אותי", "he": "אותו", "she": "אותה",
                           "we": "אותנו", "they": "אותם"}
            self_he = pronoun_map.get(subj["en"])
            if self_he:
                pool = [p for p in pool if p[0] != self_he]
            if not pool:
                return None
        return pick(pool)
    return None

def en_does(subj):
    return "does" if subj["is3sg"] else "do"

def en_doesnt(subj):
    return "doesn't" if subj["is3sg"] else "don't"

def en_pres(verb, subj):
    return verb["en"][1] if subj["is3sg"] else verb["en"][0]

def en_base(verb):
    return verb["en"][0]

def en_past(verb):
    return verb["en"][2]

def cap(s):
    return s[0].upper() + s[1:] if s else s

def en_lower(s):
    """Lowercase but preserve 'I' as uppercase."""
    return s if s == "I" else s.lower()

def en_be(subj, contraction=False):
    """Return correct form of 'to be' for subject."""
    be = {"I": "am", "he": "is", "she": "is", "we": "are", "they": "are"}
    form = be.get(subj["en"], "are")
    if contraction:
        c = {"am": "'m", "is": "'s", "are": "'re"}
        return c[form]
    return form

def get_pred_adj(subj):
    """Get a gender-agreeing predicate adjective for subject."""
    opts = []
    for a in PRED_ADJ:
        if subj["g"] == "m" and a[0] is not None:
            opts.append((a[0], a[1], a[4]))
        elif subj["g"] == "f" and a[2] is not None:
            opts.append((a[2], a[3], a[4]))
    return pick(opts) if opts else None

def sent(he, tr, en):
    return {"hebrew": he, "transliteration": tr, "english": en}

def valid_present_pairs(verb):
    """Return list of (subject, verb_form) pairs valid for present tense."""
    pairs = []
    for s in SUBJECTS:
        form = verb["pres"].get(s["pk"])
        if form:
            pairs.append((s, form))
    return pairs

def valid_past_pairs(verb):
    pairs = []
    for s in SUBJECTS:
        form = verb["past"].get(s["ppk"])
        if form:
            pairs.append((s, form))
    return pairs

# === TEMPLATES ===

def present_with_object():
    """[subject] [present verb] [object] — He drinks coffee"""
    verbs = [v for v in VERBS if v["pres"] and v["comp"] not in
             ("about", "about_it", "quote", "time_or_loc", "location", "destination", "country")
             and v["en"][0] not in _MODAL_VERBS]
    v = pick(verbs)
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} {vf[0]} {comp[0]}",
        f"{subj['tr']} {vf[1]} {comp[1]}",
        f"{cap(subj['en'])} {en_pres(v, subj)} {comp[2]}"
    )

def present_intransitive():
    """[subject] [present verb] [location/time] — He works at the office"""
    verbs = [v for v in VERBS if v["pres"] and v["comp"] in ("time_or_loc", "location", "country")]
    v = pick(verbs)
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} {vf[0]} {comp[0]}",
        f"{subj['tr']} {vf[1]} {comp[1]}",
        f"{cap(subj['en'])} {en_pres(v, subj)} {comp[2]}"
    )

def past_with_object():
    """[subject] [past verb] [object] — He wrote an email"""
    verbs = [v for v in VERBS if v["past"] and v["comp"] not in
             ("about", "about_it", "time_or_loc", "location", "destination", "country")
             and v["en"][0] not in _MODAL_VERBS]
    v = pick(verbs)
    pairs = valid_past_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} {vf[0]} {comp[0]}",
        f"{subj['tr']} {vf[1]} {comp[1]}",
        f"{cap(subj['en'])} {en_past(v)} {comp[2]}"
    )

def past_intransitive():
    """[subject] [past verb] [location] — He worked yesterday"""
    verbs = [v for v in VERBS if v["past"] and v["comp"] in ("time_or_loc", "location", "country")]
    v = pick(verbs)
    pairs = valid_past_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    return sent(
        f"{subj['he']} {vf[0]} {comp[0]}",
        f"{subj['tr']} {vf[1]} {comp[1]}",
        f"{cap(subj['en'])} {en_past(v)} {comp[2]}"
    )

def past_direction():
    """[subject] [past motion verb] [destination] — She flew to Spain"""
    verbs = [v for v in VERBS if v["past"] and v["comp"] == "destination"]
    v = pick(verbs)
    pairs = valid_past_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    dest = pick(DESTINATIONS)
    return sent(
        f"{subj['he']} {vf[0]} {dest[0]}",
        f"{subj['tr']} {vf[1]} {dest[1]}",
        f"{cap(subj['en'])} {en_past(v)} {dest[2]}"
    )

def nominal_adj():
    """[subject] [adjective] — He's tired / She's hungry"""
    subj = pick([s for s in SUBJECTS if s["pk"] in ("ms", "fs")])
    opts = []
    for a in PRED_ADJ:
        if subj["g"] == "m" and a[0]:
            opts.append((a[0], a[1], a[4]))
        elif subj["g"] == "f" and a[2]:
            opts.append((a[2], a[3], a[4]))
    if not opts:
        return None
    adj = pick(opts)
    return sent(
        f"{subj['he']} {adj[0]}",
        f"{subj['tr']} {adj[1]}",
        f"{cap(subj['en'])} {en_be(subj)} {adj[2]}"
    )

def nominal_ze():
    """זה [adjective] — It's complicated"""
    adj = pick(ZE_ADJ)
    return sent(f"זה {adj[0]}", f"ze {adj[1]}", f"It's {adj[2]}")

def nominal_location():
    """[subject] [location] — I'm at the office"""
    subj = pick(SUBJECTS)
    loc = pick(LOCATIONS)
    return sent(
        f"{subj['he']} {loc[0]}",
        f"{subj['tr']} {loc[1]}",
        f"{cap(subj['en'])}{en_be(subj, contraction=True)} {loc[2]}"
    )

def past_haya():
    """[subject] היה [adjective] — He was tired"""
    subj = pick([s for s in SUBJECTS if s["ppk"] in ("3ms", "3fs")])
    haya = ("היה", "haya") if subj["g"] == "m" else ("היתה", "hayta")
    adj = get_pred_adj(subj)
    if not adj:
        return None
    return sent(
        f"{subj['he']} {haya[0]} {adj[0]}",
        f"{subj['tr']} {haya[1]} {adj[1]}",
        f"{cap(subj['en'])} was {adj[2]}"
    )

def ze_haya():
    """זה היה [adjective] — It was amazing"""
    adj = pick(ZE_ADJ)
    return sent(f"זה היה {adj[0]}", f"ze haya {adj[1]}", f"It was {adj[2]}")

def want_inf():
    """[subject] רוצה/רוצים [infinitive] — I want to eat"""
    subj = pick(SUBJECTS)
    inf = pick(INFINITIVES)
    rotse = ("רוצים", "rotsim") if subj["pk"] == "mp" else ("רוצה", "rotse")
    parts_he = [subj["he"], rotse[0], inf[0]]
    parts_tr = [subj["tr"], rotse[1], inf[1]]
    en = f"{cap(subj['en'])} want{'s' if subj['is3sg'] else ''} {inf[2]}"
    if inf[4] == "destination":
        d = pick(DESTINATIONS)
        parts_he.append(d[0]); parts_tr.append(d[1])
        en += f" {d[2]}"
    elif inf[4] == "location":
        l = pick(LOCATIONS)
        parts_he.append(l[0]); parts_tr.append(l[1])
        en += f" {l[2]}"
    return sent(" ".join(parts_he), " ".join(parts_tr), en)

def can_inf():
    """[subject] יכול/ה [infinitive]? — Can you come?"""
    subj = pick([s for s in SUBJECTS if s["pk"] in ("ms", "fs")])
    yakhol = ("יכול", "yakhol") if subj["g"] == "m" else ("יכולה", "yekhola")
    inf = pick(INFINITIVES)
    parts_he = [subj["he"], yakhol[0], inf[0]]
    parts_tr = [subj["tr"], yakhol[1], inf[1]]
    en = f"Can {en_lower(subj['en'])} {inf[2].replace('to ', '')}?"
    if inf[4] == "destination":
        d = pick(DESTINATIONS)
        parts_he.append(d[0]); parts_tr.append(d[1])
        en = en[:-1] + f" {d[2]}?"
    he = " ".join(parts_he) + "?"
    tr = " ".join(parts_tr) + "?"
    return sent(he, tr, en)

def like_inf():
    """[subject] אוהב/ת [infinitive] — She likes eating"""
    subj = pick(SUBJECTS)
    ohev = {"ms": ("אוהב", "ohev"), "fs": ("אוהבת", "ohevet"), "mp": ("אוהבים", "ohavim")}
    form = ohev.get(subj["pk"])
    if not form:
        return None
    inf = pick(INFINITIVES)
    parts_he = [subj["he"], form[0], inf[0]]
    parts_tr = [subj["tr"], form[1], inf[1]]
    en = f"{cap(subj['en'])} like{'s' if subj['is3sg'] else ''} {inf[3]}"
    if inf[4] == "destination":
        d = pick(DESTINATIONS)
        parts_he.append(d[0]); parts_tr.append(d[1])
        en += f" {d[2]}"
    return sent(" ".join(parts_he), " ".join(parts_tr), en)

def like_object():
    """[subject] אוהב/ת [object] — He likes sushi"""
    subj = pick(SUBJECTS)
    ohev = {"ms": ("אוהב", "ohev"), "fs": ("אוהבת", "ohevet"), "mp": ("אוהבים", "ohavim")}
    form = ohev.get(subj["pk"])
    if not form:
        return None
    obj = pick(FOOD + DRINK + [["סושי", "sushi", "sushi"], ["קפה", "kafe", "coffee"]])
    return sent(
        f"{subj['he']} {form[0]} {obj[0]}",
        f"{subj['tr']} {form[1]} {obj[1]}",
        f"{cap(subj['en'])} like{'s' if subj['is3sg'] else ''} {obj[2]}"
    )

def q_what_present():
    """מה [subject] [present verb]? — What do you drink?"""
    verbs = [v for v in VERBS if v["pres"] and v["comp"] not in
             ("about", "about_it", "quote", "location", "country", "destination", "time_or_loc",
              "person", "person_obj")
             and v["en"][0] not in _MODAL_VERBS]
    v = pick(verbs)
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    en = f"What {en_does(subj)} {en_lower(subj['en'])} {en_base(v)}?"
    return sent(f"מה {subj['he']} {vf[0]}?", f"ma {subj['tr']} {vf[1]}?", en)

def q_what_past():
    """מה [subject] [past verb]? — What did he eat?"""
    verbs = [v for v in VERBS if v["past"] and v["comp"] not in
             ("about", "about_it", "quote", "location", "country", "destination", "time_or_loc",
              "person", "person_obj")
             and v["en"][0] not in _MODAL_VERBS]
    v = pick(verbs)
    pairs = valid_past_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    time = pick(PAST_TIMES + [None, None, None])
    he = f"מה {subj['he']} {vf[0]}"
    tr = f"ma {subj['tr']} {vf[1]}"
    en = f"What did {en_lower(subj['en'])} {en_base(v)}"
    if time:
        he += f" {time[0]}"
        tr += f" {time[1]}"
        en += f" {time[2]}"
    return sent(he + "?", tr + "?", en + "?")

def q_where():
    """איפה [subject] [verb]? — Where does he work?"""
    verbs = [v for v in VERBS if v["comp"] in ("time_or_loc", "location", "country")]
    v = pick(verbs)
    # try present first
    pairs = valid_present_pairs(v)
    if pairs:
        subj, vf = pick(pairs)
        return sent(
            f"איפה {subj['he']} {vf[0]}?",
            f"eifo {subj['tr']} {vf[1]}?",
            f"Where {en_does(subj)} {en_lower(subj['en'])} {en_base(v)}?"
        )
    pairs = valid_past_pairs(v)
    if pairs:
        subj, vf = pick(pairs)
        return sent(
            f"איפה {subj['he']} {vf[0]}?",
            f"eifo {subj['tr']} {vf[1]}?",
            f"Where did {en_lower(subj['en'])} {en_base(v)}?"
        )
    return None

def q_where_to():
    """לאן [subject] [motion verb]? — Where are they going?"""
    verbs = [v for v in VERBS if v["comp"] == "destination"]
    v = pick(verbs)
    pairs = valid_present_pairs(v) or valid_past_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    is_past = vf in [f for f in v["past"].values()]
    if is_past:
        return sent(
            f"לאן {subj['he']} {vf[0]}?",
            f"le'an {subj['tr']} {vf[1]}?",
            f"Where did {en_lower(subj['en'])} {en_base(v)} to?"
        )
    return sent(
        f"לאן {subj['he']} {vf[0]}?",
        f"le'an {subj['tr']} {vf[1]}?",
        f"Where {en_be(subj)} {en_lower(subj['en'])} {v['en'][4]}?"
    )

def q_when():
    """מתי [noun phrase]? — When is your flight?"""
    _when_nouns = [n for n in SHEL_NOUNS if n[2] in ("flight", "class")]
    if not _when_nouns:
        return None
    noun = pick(_when_nouns)
    shel = pick(SHEL)
    return sent(
        f"מתי {noun[0]} {shel[0]}?",
        f"matai {noun[1]} {shel[1]}?",
        f"When is {shel[2]} {noun[2]}?"
    )

def q_why():
    """למה [subject] (לא) [verb]? — Why aren't you eating?"""
    v = pick([v for v in VERBS if v["pres"] and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    if random.random() < 0.5:
        # negative
        return sent(
            f"למה {subj['he']} לא {vf[0]} {comp[0]}?",
            f"lama {subj['tr']} lo {vf[1]} {comp[1]}?",
            f"Why {en_doesnt(subj)} {en_lower(subj['en'])} {en_base(v)} {comp[2]}?"
        )
    else:
        return sent(
            f"למה {subj['he']} {vf[0]} {comp[0]}?",
            f"lama {subj['tr']} {vf[1]} {comp[1]}?",
            f"Why {en_does(subj)} {en_lower(subj['en'])} {en_base(v)} {comp[2]}?"
        )

def q_how():
    """איך [noun שלך]? — How is your dessert?"""
    noun = pick(SHEL_NOUNS)
    shel = pick(SHEL)
    return sent(
        f"איך {noun[0]} {shel[0]}?",
        f"eikh {noun[1]} {shel[1]}?",
        f"How is {shel[2]} {noun[2]}?"
    )

def negation_present():
    """[subject] לא [present verb] [object] — He doesn't eat fish"""
    v = pick([v for v in VERBS if v["pres"] and v["comp"] in COMP_MAP
              and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} לא {vf[0]} {comp[0]}",
        f"{subj['tr']} lo {vf[1]} {comp[1]}",
        f"{cap(subj['en'])} {en_doesnt(subj)} {en_base(v)} {comp[2]}"
    )

def negation_past():
    """[subject] לא [past verb] [object] — She didn't eat anything"""
    v = pick([v for v in VERBS if v["past"] and v["comp"] not in ("about", "about_it")
              and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_past_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    if random.random() < 0.4:
        return sent(
            f"{subj['he']} לא {vf[0]} כלום",
            f"{subj['tr']} lo {vf[1]} klum",
            f"{cap(subj['en'])} didn't {en_base(v)} anything"
        )
    else:
        comp = get_comp(v, subj)
        if not comp:
            return None
        return sent(
            f"{subj['he']} לא {vf[0]} {comp[0]}",
            f"{subj['tr']} lo {vf[1]} {comp[1]}",
            f"{cap(subj['en'])} didn't {en_base(v)} {comp[2]}"
        )

def too_adj():
    """זה [adj] מדי — It's too sweet"""
    adj = pick(MIDI_ADJ)
    return sent(f"זה {adj[0]} מדי", f"ze {adj[1]} midai", f"It's too {adj[2]}")

def already_past():
    """[subject] כבר [past verb] — I already ate"""
    v = pick([v for v in VERBS if v["past"] and v["comp"] in COMP_MAP
              and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_past_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} כבר {vf[0]} {comp[0]}",
        f"{subj['tr']} kvar {vf[1]} {comp[1]}",
        f"{cap(subj['en'])} already {en_past(v)} {comp[2]}"
    )

def possession():
    """יש ל[person] [noun] [adj] — He has a new phone"""
    yl = pick(YESH_L)
    noun = pick(POSSESSABLE)
    if random.random() < 0.5 and POSS_MOD:
        mod = pick(POSS_MOD)
        return sent(
            f"יש {yl[0]} {noun[0]} {mod[0]}",
            f"yesh {yl[1]} {noun[1]} {mod[1]}",
            f"{cap(yl[2])} {'has' if yl[2] in ('he','she') else 'have'} a {mod[2]} {noun[2]}"
        )
    return sent(
        f"יש {yl[0]} {noun[0]}",
        f"yesh {yl[1]} {noun[1]}",
        f"{cap(yl[2])} {'has' if yl[2] in ('he','she') else 'have'} a {noun[2]}"
    )

def think_that():
    """[subject] חושב/ת ש[כן/לא] — I think so"""
    subj = pick(SUBJECTS)
    form = {"ms": ("חושב", "khoshev"), "fs": ("חושבת", "khoshevet")}.get(subj["pk"])
    if not form:
        return None
    if random.random() < 0.5:
        return sent(
            f"{subj['he']} {form[0]} שכן",
            f"{subj['tr']} {form[1]} shakhen",
            f"{cap(subj['en'])} think{'s' if subj['is3sg'] else ''} so"
        )
    return sent(
        f"{subj['he']} {form[0]} שלא",
        f"{subj['tr']} {form[1]} shelo",
        f"{cap(subj['en'])} {'doesn' + chr(39) + 't' if subj['is3sg'] else 'don' + chr(39) + 't'} think so"
    )

def sure_that():
    """[subject] בטוח/ה ש[clause] — He's sure the door is open"""
    subj = pick([s for s in SUBJECTS if s["ppk"] in ("3ms", "3fs", "1s")])
    bt = ("בטוח", "batuakh") if subj["g"] == "m" else ("בטוחה", "betukha")
    cl = pick(_SURE_CLAUSES)
    be = "'s" if subj["is3sg"] else ("'m" if subj["en"] == "I" else "'re")
    return sent(
        f"{subj['he']} {bt[0]} {cl[0]}",
        f"{subj['tr']} {bt[1]} {cl[1]}",
        f"{cap(subj['en'])}{be} sure {cl[2]}"
    )

def because_of():
    """[clause] בגלל [noun] — He's stressed because of the boss"""
    subj = pick([s for s in SUBJECTS if s["g"] == "m" and s["pk"] == "ms"])
    state = pick(_BECAUSE_STATES)
    cause = pick(_BECAUSE_CAUSES)
    be = "'s" if subj["is3sg"] else ("'m" if subj["en"] == "I" else "'re")
    return sent(
        f"{subj['he']} {state[0]} בגלל {cause[0]}",
        f"{subj['tr']} {state[1]} biglal {cause[1]}",
        f"{cap(subj['en'])}{be} {state[2]} because of {cause[2]}"
    )

def never_pres():
    """[subject] אף פעם לא [present verb] — He never drinks coffee"""
    v = pick([v for v in VERBS if v["pres"] and v["comp"] in COMP_MAP
              and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} אף פעם לא {vf[0]} {comp[0]}",
        f"{subj['tr']} af pa'am lo {vf[1]} {comp[1]}",
        f"{cap(subj['en'])} never {en_base(v)}{'s' if subj['is3sg'] else ''} {comp[2]}"
    )

def not_so():
    """[subject] לא כל כך [adj] — She's not so hungry"""
    subj = pick([s for s in SUBJECTS if s["pk"] in ("ms", "fs")])
    opts = []
    for a in PRED_ADJ:
        if subj["g"] == "m" and a[0]:
            opts.append((a[0], a[1], a[4]))
        elif subj["g"] == "f" and a[2]:
            opts.append((a[2], a[3], a[4]))
    if not opts:
        return None
    adj = pick(opts)
    return sent(
        f"{subj['he']} לא כל כך {adj[0]}",
        f"{subj['tr']} lo kol kakh {adj[1]}",
        f"{cap(subj['en'])} {'isn' + chr(39) + 't' if subj['is3sg'] else ('am not' if subj['en']=='I' else 'aren' + chr(39) + 't')} so {adj[2]}"
    )

def temporal_past():
    """[time] [subject] [past verb] [comp] — Yesterday he went to the beach"""
    time = pick(PAST_TIMES)
    v = pick([v for v in VERBS if v["past"] and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_past_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    he = f"{time[0]} {subj['he']} {vf[0]}"
    tr = f"{time[1]} {subj['tr']} {vf[1]}"
    en = f"{cap(time[2])} {en_lower(subj['en'])} {en_past(v)}"
    if comp:
        he += f" {comp[0]}"; tr += f" {comp[1]}"; en += f" {comp[2]}"
    return sent(he, tr, en)

def frequency():
    """[subject] [present verb] [X] פעמים ב[time] — He eats twice a day"""
    _freq_comps = ("food", "drink", "activity", "seeable", "buyable", "sendable")
    v = pick([v for v in VERBS if v["pres"] and v["comp"] in _freq_comps
              and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    f_ = pick(_FREQ_COUNTS)
    p = pick(_FREQ_PERIODS)
    return sent(
        f"{subj['he']} {vf[0]} {comp[0]} {f_[0]} {p[0]}",
        f"{subj['tr']} {vf[1]} {comp[1]} {f_[1]} {p[1]}",
        f"{cap(subj['en'])} {en_pres(v, subj)} {comp[2]} {f_[2]} {p[2]}"
    )

def def_noun_phrase():
    """ה[noun] ה[adj] — The new computer"""
    np = pick(DEF_NP)
    return sent(
        f"{np[0]} {np[3]}",
        f"{np[1]} {np[4]}",
        f"The {np[5]} {np[2].replace('the ', '')}"
    )

def even_past():
    """אפילו [subject] [past verb] — Even Madonna studied Hebrew"""
    name = pick(_EVEN_NAMES)
    if name[3] == "f":
        verbs_opts = _EVEN_VERBS_F
    else:
        verbs_opts = _EVEN_VERBS_M
    vo = pick(verbs_opts)
    obj = pick([["עברית", "ivrit", "Hebrew"], None, None])
    he = f"אפילו {name[0]} {vo[0][0]}"
    tr = f"afilu {name[1]} {vo[0][1]}"
    en = f"Even {name[2]} {vo[1]}"
    if obj:
        he += f" {obj[0]}"; tr += f" {obj[1]}"; en += f" {obj[2]}"
    return sent(he, tr, en)

def emphatic():
    """[subject] כן [past verb]! — I DID work yesterday!"""
    v = pick([v for v in VERBS if v["past"] and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_past_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    time = pick(TIME_WORDS[:2])
    return sent(
        f"{subj['he']} כן {vf[0]} {time[0]}!",
        f"{subj['tr']} ken {vf[1]} {time[1]}!",
        f"{cap(subj['en'])} DID {en_base(v)} {time[2]}!"
    )

def shel_question():
    """של מי ה[noun]? — Whose is the phone?"""
    noun = pick(SHEL_NOUNS)
    return sent(
        f"של מי {noun[0]}?",
        f"shel mi {noun[1]}?",
        f"Whose {noun[2]} is it?"
    )

def nobody_nothing():
    """אף אחד/שום דבר לא [adj] — Nobody's perfect"""
    adj = pick(ZE_ADJ)
    o = pick(_NOBODY_OPENERS)
    return sent(f"{o[0]} {adj[0]}", f"{o[1]} {adj[1]}", f"{o[2]} {adj[2]}")

# === NEW TEMPLATES ===

_NEED_FORMS = _TD["need_inf_forms"]
_FEEL_LIKE = _TD["feel_like_forms"]
_POSSIBLE_COMPS = _TD["possible_complements"]
_COULD_BE = _TD["could_be_phrases"]
_ABOUT_TOPICS = _TD["about_topics"]
_COUNTABLE = _TD["countable_nouns"]
_ADV = _TD["adverbs"]
_FIXED = _TD["fixed_expressions"]


def need_inf():
    """[subject] צריך/ה [infinitive] — I need to eat"""
    subj = pick([s for s in SUBJECTS if s["pk"] in ("ms", "fs")])
    form = _NEED_FORMS["ms"] if subj["g"] == "m" else _NEED_FORMS["fs"]
    inf = pick(INFINITIVES)
    parts_he = [subj["he"], form[0], inf[0]]
    parts_tr = [subj["tr"], form[1], inf[1]]
    en = f"{cap(subj['en'])} need{'s' if subj['is3sg'] else ''} {inf[2]}"
    if inf[4] == "destination":
        d = pick(DESTINATIONS)
        parts_he.append(d[0]); parts_tr.append(d[1])
        en += f" {d[2]}"
    elif inf[4] == "location":
        loc = pick(LOCATIONS)
        parts_he.append(loc[0]); parts_tr.append(loc[1])
        en += f" {loc[2]}"
    return sent(" ".join(parts_he), " ".join(parts_tr), en)


def yes_no_question():
    """[present sentence]? — Do you work here?"""
    v = pick([v for v in VERBS if v["pres"] and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if comp:
        return sent(
            f"{subj['he']} {vf[0]} {comp[0]}?",
            f"{subj['tr']} {vf[1]} {comp[1]}?",
            f"{en_does(subj).capitalize()} {en_lower(subj['en'])} {en_base(v)} {comp[2]}?"
        )
    return None


def feel_like():
    """בא ל[person] [infinitive] — I feel like eating"""
    fl = pick(_FEEL_LIKE)
    inf = pick(INFINITIVES)
    parts_he = [fl[0], inf[0]]
    parts_tr = [fl[1], inf[1]]
    en = f"{cap(fl[2])} feel{'s' if fl[2] in ('he', 'she') else ''} like {inf[3]}"
    if inf[4] == "destination":
        d = pick(DESTINATIONS)
        parts_he.append(d[0]); parts_tr.append(d[1])
        en += f" {d[2]}"
    return sent(" ".join(parts_he), " ".join(parts_tr), en)


def possible_inf():
    """אפשר [infinitive]? — Is it possible to sit here?"""
    inf = pick(_POSSIBLE_COMPS)
    loc = pick(LOCATIONS) if random.random() < 0.4 else None
    he = f"אפשר {inf[0]}"
    tr = f"efshar {inf[1]}"
    en = f"Is it possible {inf[2]}"
    if loc:
        he += f" {loc[0]}"
        tr += f" {loc[1]}"
        en += f" {loc[2]}"
    return sent(he + "?", tr + "?", en + "?")


def could_be():
    """יכול להיות / לא יכול להיות — Could be / No way"""
    phrase = pick(_COULD_BE)
    return sent(phrase[0], phrase[1], phrase[2])


def q_how_many():
    """כמה [noun] יש ל[person]? — How many cats do you have?"""
    noun = pick(_COUNTABLE)
    yl = pick(YESH_L)
    return sent(
        f"כמה {noun[0]} יש {yl[0]}?",
        f"kama {noun[1]} yesh {yl[1]}?",
        f"How many {noun[2]} {'does' if yl[2] in ('he','she') else 'do'} {en_lower(yl[2])} have?"
    )


def q_about():
    """על מה/מי [subject] [verb]? — What are you talking about?"""
    topic = pick(_ABOUT_TOPICS)
    v = pick([v for v in VERBS if v["comp"] in ("about", "about_it")])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    return sent(
        f"{topic[0]} {subj['he']} {vf[0]}?",
        f"{topic[1]} {subj['tr']} {vf[1]}?",
        f"{topic[2]} {en_be(subj)} {en_lower(subj['en'])} {v['en'][4]}?"
    )


def still_pres():
    """[subject] עדיין [present verb] — He still works here"""
    adv = _ADV["still"]
    v = pick([v for v in VERBS if v["pres"] and v["comp"] in
             ("time_or_loc", "location", "country")])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} {adv[0]} {vf[0]} {comp[0]}",
        f"{subj['tr']} {adv[1]} {vf[1]} {comp[1]}",
        f"{cap(subj['en'])} {adv[2]} {en_pres(v, subj)} {comp[2]}"
    )


def still_adj():
    """[subject] עדיין [adjective] — She's still tired"""
    adv = _ADV["still"]
    subj = pick([s for s in SUBJECTS if s["pk"] in ("ms", "fs")])
    adj = get_pred_adj(subj)
    if not adj:
        return None
    return sent(
        f"{subj['he']} {adv[0]} {adj[0]}",
        f"{subj['tr']} {adv[1]} {adj[1]}",
        f"{cap(subj['en'])}{en_be(subj, contraction=True)} {adv[2]} {adj[2]}"
    )


def almost_past():
    """[subject] כמעט [past verb] — I almost ate the cake"""
    adv = _ADV["almost"]
    v = pick([v for v in VERBS if v["past"] and v["comp"] in COMP_MAP])
    pairs = valid_past_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} {adv[0]} {vf[0]} {comp[0]}",
        f"{subj['tr']} {adv[1]} {vf[1]} {comp[1]}",
        f"{cap(subj['en'])} {adv[2]} {en_past(v)} {comp[2]}"
    )


def again_more():
    """[subject] [verb] עוד [object] — He eats more bread"""
    adv = _ADV["again"]
    v = pick([v for v in VERBS if v["pres"] and v["comp"] in
             ("food", "drink")])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} {vf[0]} {adv[0]} {comp[0]}",
        f"{subj['tr']} {vf[1]} {adv[1]} {comp[1]}",
        f"{cap(subj['en'])} {en_pres(v, subj)} more {comp[2]}"
    )


def when_clause():
    """כש[subject] [past verb] [comp], [subject] [past verb] [comp]"""
    v1 = pick([v for v in VERBS if v["past"] and v["en"][0] not in _MODAL_VERBS])
    v2 = pick([v for v in VERBS if v["past"] and v != v1 and v["en"][0] not in _MODAL_VERBS])
    pairs1 = valid_past_pairs(v1)
    pairs2 = valid_past_pairs(v2)
    if not pairs1 or not pairs2:
        return None
    subj1, vf1 = pick(pairs1)
    subj2, vf2 = pick(pairs2)
    comp1 = get_comp(v1, subj1)
    comp2 = get_comp(v2, subj2)
    he = f"כש{subj1['he']} {vf1[0]}"
    tr = f"kshe{subj1['tr']} {vf1[1]}"
    en = f"When {en_lower(subj1['en'])} {en_past(v1)}"
    if comp1:
        he += f" {comp1[0]}"; tr += f" {comp1[1]}"; en += f" {comp1[2]}"
    he += f", {subj2['he']} {vf2[0]}"
    tr += f", {subj2['tr']} {vf2[1]}"
    en += f", {en_lower(subj2['en'])} {en_past(v2)}"
    if comp2:
        he += f" {comp2[0]}"; tr += f" {comp2[1]}"; en += f" {comp2[2]}"
    return sent(he, tr, en)


def always_pres():
    """[subject] תמיד [present verb] [object] — She always drinks coffee"""
    adv = _ADV["always"]
    v = pick([v for v in VERBS if v["pres"] and v["comp"] in COMP_MAP
              and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} {adv[0]} {vf[0]} {comp[0]}",
        f"{subj['tr']} {adv[1]} {vf[1]} {comp[1]}",
        f"{cap(subj['en'])} {adv[2]} {en_pres(v, subj)} {comp[2]}"
    )


def sometimes_pres():
    """[subject] לפעמים [present verb] — I sometimes eat sushi"""
    adv = _ADV["sometimes"]
    v = pick([v for v in VERBS if v["pres"] and v["comp"] in COMP_MAP
              and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} {adv[0]} {vf[0]} {comp[0]}",
        f"{subj['tr']} {adv[1]} {vf[1]} {comp[1]}",
        f"{cap(subj['en'])} {adv[2]} {en_pres(v, subj)} {comp[2]}"
    )


def only_object():
    """[subject] [verb] רק [object] — I only drink water"""
    adv = _ADV["only"]
    v = pick([v for v in VERBS if v["pres"] and v["comp"] in
             ("food", "drink")])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    comp = get_comp(v, subj)
    if not comp:
        return None
    return sent(
        f"{subj['he']} {vf[0]} {adv[0]} {comp[0]}",
        f"{subj['tr']} {vf[1]} {adv[1]} {comp[1]}",
        f"{cap(subj['en'])} {adv[2]} {en_pres(v, subj)} {comp[2]}"
    )


def a_lot_pres():
    """[subject] [verb] הרבה — He works a lot"""
    adv = _ADV["a_lot"]
    v = pick([v for v in VERBS if v["pres"] and v["comp"] in
             ("time_or_loc", "activity") and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_present_pairs(v)
    if not pairs:
        return None
    subj, vf = pick(pairs)
    return sent(
        f"{subj['he']} {vf[0]} {adv[0]}",
        f"{subj['tr']} {vf[1]} {adv[1]}",
        f"{cap(subj['en'])} {en_pres(v, subj)} {adv[2]}"
    )


def together_past():
    """[subject] [past verb] יחד — We worked together"""
    adv = _ADV["together"]
    v = pick([v for v in VERBS if v["past"] and v["en"][0] not in _MODAL_VERBS])
    pairs = valid_past_pairs(v)
    if not pairs:
        return None
    # "together" only makes sense with plural subjects
    plural = [(s, f) for s, f in pairs if s["pk"] == "mp" or s["en"] in ("we", "they")]
    if not plural:
        return None
    subj, vf = pick(plural)
    comp = get_comp(v, subj)
    he = f"{subj['he']} {vf[0]}"
    tr = f"{subj['tr']} {vf[1]}"
    en = f"{cap(subj['en'])} {en_past(v)}"
    if comp:
        he += f" {comp[0]}"; tr += f" {comp[1]}"; en += f" {comp[2]}"
    he += f" {adv[0]}"; tr += f" {adv[1]}"; en += f" {adv[2]}"
    return sent(he, tr, en)


def fixed_expression():
    """Common fixed expressions — What's up?"""
    expr = pick(_FIXED)
    return sent(expr[0], expr[1], expr[2])


# === MAIN ===

TEMPLATES = [
    (present_with_object, 10),
    (present_intransitive, 6),
    (past_with_object, 10),
    (past_intransitive, 5),
    (past_direction, 6),
    (nominal_adj, 6),
    (nominal_ze, 4),
    (nominal_location, 4),
    (past_haya, 5),
    (ze_haya, 4),
    (want_inf, 8),
    (can_inf, 6),
    (like_inf, 6),
    (like_object, 5),
    (q_what_present, 7),
    (q_what_past, 6),
    (q_where, 5),
    (q_where_to, 4),
    (q_when, 3),
    (q_why, 5),
    (q_how, 3),
    (negation_present, 7),
    (negation_past, 5),
    (too_adj, 4),
    (already_past, 5),
    (possession, 5),
    (think_that, 4),
    (sure_that, 3),
    (because_of, 3),
    (never_pres, 4),
    (not_so, 4),
    (temporal_past, 5),
    (frequency, 4),
    (def_noun_phrase, 3),
    (even_past, 3),
    (emphatic, 3),
    (shel_question, 3),
    (nobody_nothing, 3),
    (need_inf, 7),
    (yes_no_question, 6),
    (feel_like, 5),
    (possible_inf, 3),
    (could_be, 2),
    (q_how_many, 4),
    (q_about, 3),
    (still_pres, 4),
    (still_adj, 3),
    (almost_past, 4),
    (again_more, 3),
    (when_clause, 4),
    (always_pres, 5),
    (sometimes_pres, 4),
    (only_object, 3),
    (a_lot_pres, 3),
    (together_past, 3),
    (fixed_expression, 3),
]

_funcs, _weights = zip(*TEMPLATES)

def generate():
    """Generate one random sentence. Retries on None."""
    for _ in range(20):
        fn = random.choices(_funcs, weights=_weights, k=1)[0]
        result = fn()
        if result:
            return result
    # fallback
    return sent("בדרך כלל", "baderekh klal", "Usually")

def generate_batch(n=20):
    return [generate() for _ in range(n)]
