#!/usr/bin/env python3
"""One-time export: extract generator.py data constants to generator_data.json."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generator as g


def convert(obj):
    """Recursively convert tuples to lists for JSON serialization."""
    if isinstance(obj, tuple):
        return [convert(x) for x in obj]
    if isinstance(obj, list):
        return [convert(x) for x in obj]
    if isinstance(obj, dict):
        return {k: convert(v) for k, v in obj.items()}
    return obj


data = {
    "subjects": convert(g.SUBJECTS),
    "verbs": convert(g.VERBS),
    "study_verb": convert(g.STUDY_VERB),
    "complements": {
        "food": convert(g.FOOD),
        "drink": convert(g.DRINK),
        "openable": convert(g.OPENABLE),
        "sendable": convert(g.SENDABLE),
        "activity": convert(g.ACTIVITY),
        "person_obj": convert(g.PERSON_OBJ),
        "person_et": convert(g.PERSON_ET),
        "buyable": convert(g.BUYABLE),
        "seeable": convert(g.SEEABLE),
        "writable": convert(g.WRITABLE),
        "puttable": convert(g.PUTTABLE),
        "quote": convert(g.QUOTE),
        "about_it": convert(g.ABOUT_IT),
    },
    "locations": convert(g.LOCATIONS),
    "destinations": convert(g.DESTINATIONS),
    "countries": convert(g.COUNTRIES),
    "time_words": convert(g.TIME_WORDS),
    "present_times": convert(g.PRESENT_TIMES),
    "past_times": [["אתמול", "etmol", "yesterday"], ["היום", "hayom", "today"]],
    "adjectives": {
        "predicate": convert(g.PRED_ADJ),
        "ze": convert(g.ZE_ADJ),
        "midi": convert(g.MIDI_ADJ),
        "definite_np": convert(g.DEF_NP),
    },
    "possession": {
        "possessable": convert(g.POSSESSABLE),
        "yesh_l": convert(g.YESH_L),
        "modifiers": convert(g.POSS_MOD),
        "shel": convert(g.SHEL),
        "shel_nouns": convert(g.SHEL_NOUNS),
    },
    "infinitives": convert(g.INFINITIVES),
    "template_data": {
        "even_past_names": [
            ["מדונה", "madonna", "Madonna", "f"],
            ["ביונסה", "beyonse", "Beyoncé", "f"],
            ["רומיאו", "romeo", "Romeo", "m"],
        ],
        "even_past_verbs_m": [
            [["למד", "lamad"], "studied"],
            [["עבד", "avad"], "worked"],
        ],
        "even_past_verbs_f": [
            [["למדה", "lamda"], "studied"],
        ],
        "sure_that_clauses": [
            ["שהדלת פתוחה", "shehadelet ptukha", "the door is open"],
            ["שהחלון פתוח", "shehakhalon patu'akh", "the window is open"],
            ["שהדלת סגורה", "shehadelet sgura", "the door is closed"],
        ],
        "because_of_causes": [
            ["הבוס", "habos", "the boss"],
            ["הבוסית", "habosit", "the boss"],
            ["האהבה", "ha'ahava", "love"],
            ["הטיסה", "hatisa", "the flight"],
        ],
        "because_of_states": [
            ["בלחץ", "belakhats", "stressed"],
            ["עייף", "ayef", "tired"],
            ["עסוק", "asuk", "busy"],
        ],
        "nobody_openers": [
            ["אף אחד לא", "af ekhad lo", "Nobody's"],
            ["שום דבר לא", "shum davar lo", "Nothing is"],
        ],
        "frequency_counts": [
            ["פעם אחת", "pa'am akhat", "once"],
            ["פעמיים", "pa'amayim", "twice"],
            ["שלוש פעמים", "shalosh pe'amim", "three times"],
        ],
        "frequency_periods": [
            ["ביום", "bayom", "a day"],
            ["בשבוע", "bashavua", "a week"],
            ["בשנה", "bashana", "a year"],
        ],
    },
}

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generator_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Exported to generator_data.json ({os.path.getsize(out)} bytes)")
