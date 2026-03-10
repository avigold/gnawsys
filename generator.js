/** Rule-based Hebrew sentence generator (TypeScript port of generator.js). */
// === DATA (populated by init()) ===
let SUBJECTS;
let VERBS;
let STUDY_VERB;
let FOOD;
let DRINK;
let OPENABLE;
let SENDABLE;
let ACTIVITY;
let PERSON_OBJ;
let PERSON_ET;
let BUYABLE;
let SEEABLE;
let WRITABLE;
let PUTTABLE;
let QUOTE;
let ABOUT_IT;
let COMP_MAP;
let LOCATIONS;
let DESTINATIONS;
let COUNTRIES;
let TIME_WORDS;
let PRESENT_TIMES;
let PAST_TIMES;
let PRED_ADJ;
let ZE_ADJ;
let MIDI_ADJ;
let DEF_NP;
let POSSESSABLE;
let YESH_L;
let POSS_MOD;
let SHEL;
let SHEL_NOUNS;
let INFINITIVES;
let _EVEN_NAMES;
let _EVEN_VERBS_M;
let _EVEN_VERBS_F;
let _SURE_CLAUSES;
let _BECAUSE_CAUSES;
let _BECAUSE_STATES;
let _NOBODY_OPENERS;
let _FREQ_COUNTS;
let _FREQ_PERIODS;
let _NEED_FORMS;
let _FEEL_LIKE;
let _POSSIBLE_COMPS;
let _COULD_BE;
let _ABOUT_TOPICS;
let _COUNTABLE;
let _ADV;
let _FIXED;
const _MODAL_VERBS = new Set(["want", "need", "start", "love"]);
// === INIT ===
/**
 * Load generator_data.json via fetch and populate all module-level data.
 * Must be called (and awaited) before generate() or generateBatch().
 * @param url - Optional URL/path to generator_data.json.
 *   Defaults to "generator_data.json" (relative to the page / worker).
 */
export async function init(url = "generator_data.json") {
    const resp = await fetch(url);
    if (!resp.ok)
        throw new Error(`Failed to load data: ${resp.status}`);
    const data = await resp.json();
    SUBJECTS = data.subjects;
    VERBS = data.verbs;
    STUDY_VERB = data.study_verb;
    const comp = data.complements;
    FOOD = comp.food;
    DRINK = comp.drink;
    OPENABLE = comp.openable;
    SENDABLE = comp.sendable;
    ACTIVITY = comp.activity;
    PERSON_OBJ = comp.person_obj;
    PERSON_ET = comp.person_et;
    BUYABLE = comp.buyable;
    SEEABLE = comp.seeable;
    WRITABLE = comp.writable;
    PUTTABLE = comp.puttable;
    QUOTE = comp.quote;
    ABOUT_IT = comp.about_it;
    COMP_MAP = {
        food: FOOD, drink: DRINK, openable: OPENABLE, sendable: SENDABLE,
        activity: ACTIVITY, person: PERSON_ET, person_obj: PERSON_OBJ,
        buyable: BUYABLE, seeable: SEEABLE, writable: WRITABLE, puttable: PUTTABLE,
        quote: QUOTE, about_it: ABOUT_IT, about: ABOUT_IT,
    };
    LOCATIONS = data.locations;
    DESTINATIONS = data.destinations;
    COUNTRIES = data.countries;
    TIME_WORDS = data.time_words;
    PRESENT_TIMES = data.present_times;
    PAST_TIMES = data.past_times;
    const adj = data.adjectives;
    PRED_ADJ = adj.predicate;
    ZE_ADJ = adj.ze;
    MIDI_ADJ = adj.midi;
    DEF_NP = adj.definite_np;
    const poss = data.possession;
    POSSESSABLE = poss.possessable;
    YESH_L = poss.yesh_l;
    POSS_MOD = poss.modifiers;
    SHEL = poss.shel;
    SHEL_NOUNS = poss.shel_nouns;
    INFINITIVES = data.infinitives;
    const td = data.template_data;
    _EVEN_NAMES = td.even_past_names;
    _EVEN_VERBS_M = td.even_past_verbs_m;
    _EVEN_VERBS_F = td.even_past_verbs_f;
    _SURE_CLAUSES = td.sure_that_clauses;
    _BECAUSE_CAUSES = td.because_of_causes;
    _BECAUSE_STATES = td.because_of_states;
    _NOBODY_OPENERS = td.nobody_openers;
    _FREQ_COUNTS = td.frequency_counts;
    _FREQ_PERIODS = td.frequency_periods;
    _NEED_FORMS = td.need_inf_forms;
    _FEEL_LIKE = td.feel_like_forms;
    _POSSIBLE_COMPS = td.possible_complements;
    _COULD_BE = td.could_be_phrases;
    _ABOUT_TOPICS = td.about_topics;
    _COUNTABLE = td.countable_nouns;
    _ADV = td.adverbs;
    _FIXED = td.fixed_expressions;
    // Load curated sentence pool (if available)
    try {
        const base = url.replace(/[^/]*$/, "");
        const curatedResp = await fetch(base + "curated_sentences.json");
        if (curatedResp.ok) {
            _curatedPool = shuffle(await curatedResp.json());
            _curatedIndex = 0;
        }
    }
    catch {
        // No curated pool available — live generation only
    }
}
// === CURATED POOL ===
let _curatedPool = [];
let _curatedIndex = 0;
function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}
// === HELPERS ===
function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}
/**
 * Weighted random index selection (equivalent to random.choices with weights).
 * Returns a single index.
 */
function weightedIndex(weights) {
    let total = 0;
    for (let i = 0; i < weights.length; i++)
        total += weights[i];
    let r = Math.random() * total;
    for (let i = 0; i < weights.length; i++) {
        r -= weights[i];
        if (r <= 0)
            return i;
    }
    return weights.length - 1;
}
function getComp(verb, subj) {
    const ct = verb.comp;
    if (ct === "time_or_loc")
        return pick([...LOCATIONS, ...PRESENT_TIMES]);
    if (ct === "location")
        return pick(LOCATIONS);
    if (ct === "destination")
        return pick(DESTINATIONS);
    if (ct === "country")
        return pick(COUNTRIES);
    if (ct in COMP_MAP) {
        let pool = COMP_MAP[ct];
        // Filter out self-referencing pronouns
        if (ct === "person_obj" && subj) {
            const pronounMap = {
                I: "\u05D0\u05D5\u05EA\u05D9", // אותי
                he: "\u05D0\u05D5\u05EA\u05D5", // אותו
                she: "\u05D0\u05D5\u05EA\u05D4", // אותה
                we: "\u05D0\u05D5\u05EA\u05E0\u05D5", // אותנו
                they: "\u05D0\u05D5\u05EA\u05DD", // אותם
            };
            const selfHe = pronounMap[subj.en];
            if (selfHe) {
                pool = pool.filter((p) => p[0] !== selfHe);
            }
            if (pool.length === 0)
                return null;
        }
        return pick(pool);
    }
    return null;
}
function enDoes(subj) {
    return subj.is3sg ? "does" : "do";
}
function enDoesnt(subj) {
    return subj.is3sg ? "doesn't" : "don't";
}
function enPres(verb, subj) {
    return subj.is3sg ? verb.en[1] : verb.en[0];
}
function enBase(verb) {
    return verb.en[0];
}
function enPast(verb) {
    return verb.en[2];
}
function cap(s) {
    if (!s)
        return s;
    return s[0].toUpperCase() + s.slice(1);
}
function enLower(s) {
    return s === "I" ? s : s.toLowerCase();
}
function enBe(subj, contraction = false) {
    const beMap = { I: "am", he: "is", she: "is", we: "are", they: "are" };
    const form = beMap[subj.en] || "are";
    if (contraction) {
        const c = { am: "'m", is: "'s", are: "'re" };
        return c[form];
    }
    return form;
}
function getPredAdj(subj) {
    const opts = [];
    for (const a of PRED_ADJ) {
        if (subj.g === "m" && a[0] !== null) {
            opts.push([a[0], a[1], a[4]]);
        }
        else if (subj.g === "f" && a[2] !== null) {
            opts.push([a[2], a[3], a[4]]);
        }
    }
    return opts.length ? pick(opts) : null;
}
function sent(he, tr, en) {
    return { hebrew: he, transliteration: tr, english: en };
}
function validPresentPairs(verb) {
    const pairs = [];
    for (const s of SUBJECTS) {
        const form = verb.pres && verb.pres[s.pk];
        if (form)
            pairs.push([s, form]);
    }
    return pairs;
}
function validPastPairs(verb) {
    const pairs = [];
    for (const s of SUBJECTS) {
        const form = verb.past && verb.past[s.ppk];
        if (form)
            pairs.push([s, form]);
    }
    return pairs;
}
// === TEMPLATES ===
function presentWithObject() {
    const verbs = VERBS.filter((v) => v.pres &&
        !["about", "about_it", "quote", "time_or_loc", "location", "destination", "country"].includes(v.comp) &&
        !_MODAL_VERBS.has(v.en[0]));
    const v = pick(verbs);
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} ${vf[0]} ${comp[0]}`, `${subj.tr} ${vf[1]} ${comp[1]}`, `${cap(subj.en)} ${enPres(v, subj)} ${comp[2]}`);
}
function presentIntransitive() {
    const verbs = VERBS.filter((v) => v.pres && ["time_or_loc", "location", "country"].includes(v.comp));
    const v = pick(verbs);
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} ${vf[0]} ${comp[0]}`, `${subj.tr} ${vf[1]} ${comp[1]}`, `${cap(subj.en)} ${enPres(v, subj)} ${comp[2]}`);
}
function pastWithObject() {
    const verbs = VERBS.filter((v) => v.past &&
        !["about", "about_it", "time_or_loc", "location", "destination", "country"].includes(v.comp) &&
        !_MODAL_VERBS.has(v.en[0]));
    const v = pick(verbs);
    const pairs = validPastPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} ${vf[0]} ${comp[0]}`, `${subj.tr} ${vf[1]} ${comp[1]}`, `${cap(subj.en)} ${enPast(v)} ${comp[2]}`);
}
function pastIntransitive() {
    const verbs = VERBS.filter((v) => v.past && ["time_or_loc", "location", "country"].includes(v.comp));
    const v = pick(verbs);
    const pairs = validPastPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    return sent(`${subj.he} ${vf[0]} ${comp[0]}`, `${subj.tr} ${vf[1]} ${comp[1]}`, `${cap(subj.en)} ${enPast(v)} ${comp[2]}`);
}
function pastDirection() {
    const verbs = VERBS.filter((v) => v.past && v.comp === "destination");
    const v = pick(verbs);
    const pairs = validPastPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const dest = pick(DESTINATIONS);
    return sent(`${subj.he} ${vf[0]} ${dest[0]}`, `${subj.tr} ${vf[1]} ${dest[1]}`, `${cap(subj.en)} ${enPast(v)} ${dest[2]}`);
}
function nominalAdj() {
    const subj = pick(SUBJECTS.filter((s) => s.pk === "ms" || s.pk === "fs"));
    const opts = [];
    for (const a of PRED_ADJ) {
        if (subj.g === "m" && a[0])
            opts.push([a[0], a[1], a[4]]);
        else if (subj.g === "f" && a[2])
            opts.push([a[2], a[3], a[4]]);
    }
    if (!opts.length)
        return null;
    const adj = pick(opts);
    return sent(`${subj.he} ${adj[0]}`, `${subj.tr} ${adj[1]}`, `${cap(subj.en)} ${enBe(subj)} ${adj[2]}`);
}
function nominalZe() {
    const adj = pick(ZE_ADJ);
    return sent(`\u05D6\u05D4 ${adj[0]}`, `ze ${adj[1]}`, `It's ${adj[2]}`);
}
function nominalLocation() {
    const subj = pick(SUBJECTS);
    const loc = pick(LOCATIONS);
    return sent(`${subj.he} ${loc[0]}`, `${subj.tr} ${loc[1]}`, `${cap(subj.en)}${enBe(subj, true)} ${loc[2]}`);
}
function pastHaya() {
    const subj = pick(SUBJECTS.filter((s) => s.ppk === "3ms" || s.ppk === "3fs"));
    const haya = subj.g === "m" ? ["\u05D4\u05D9\u05D4", "haya"] : ["\u05D4\u05D9\u05EA\u05D4", "hayta"];
    const adj = getPredAdj(subj);
    if (!adj)
        return null;
    return sent(`${subj.he} ${haya[0]} ${adj[0]}`, `${subj.tr} ${haya[1]} ${adj[1]}`, `${cap(subj.en)} was ${adj[2]}`);
}
function zeHaya() {
    const adj = pick(ZE_ADJ);
    return sent(`\u05D6\u05D4 \u05D4\u05D9\u05D4 ${adj[0]}`, `ze haya ${adj[1]}`, `It was ${adj[2]}`);
}
function wantInf() {
    const subj = pick(SUBJECTS);
    const inf = pick(INFINITIVES);
    const rotse = subj.pk === "mp"
        ? ["\u05E8\u05D5\u05E6\u05D9\u05DD", "rotsim"]
        : ["\u05E8\u05D5\u05E6\u05D4", "rotse"];
    const partsHe = [subj.he, rotse[0], inf[0]];
    const partsTr = [subj.tr, rotse[1], inf[1]];
    let en = `${cap(subj.en)} want${subj.is3sg ? "s" : ""} ${inf[2]}`;
    if (inf[4] === "destination") {
        const d = pick(DESTINATIONS);
        partsHe.push(d[0]);
        partsTr.push(d[1]);
        en += ` ${d[2]}`;
    }
    else if (inf[4] === "location") {
        const l = pick(LOCATIONS);
        partsHe.push(l[0]);
        partsTr.push(l[1]);
        en += ` ${l[2]}`;
    }
    return sent(partsHe.join(" "), partsTr.join(" "), en);
}
function canInf() {
    const subj = pick(SUBJECTS.filter((s) => s.pk === "ms" || s.pk === "fs"));
    const yakhol = subj.g === "m"
        ? ["\u05D9\u05DB\u05D5\u05DC", "yakhol"]
        : ["\u05D9\u05DB\u05D5\u05DC\u05D4", "yekhola"];
    const inf = pick(INFINITIVES);
    const partsHe = [subj.he, yakhol[0], inf[0]];
    const partsTr = [subj.tr, yakhol[1], inf[1]];
    let en = `Can ${enLower(subj.en)} ${inf[2].replace("to ", "")}?`;
    if (inf[4] === "destination") {
        const d = pick(DESTINATIONS);
        partsHe.push(d[0]);
        partsTr.push(d[1]);
        en = en.slice(0, -1) + ` ${d[2]}?`;
    }
    const he = partsHe.join(" ") + "?";
    const tr = partsTr.join(" ") + "?";
    return sent(he, tr, en);
}
function likeInf() {
    const subj = pick(SUBJECTS);
    const ohev = {
        ms: ["\u05D0\u05D5\u05D4\u05D1", "ohev"],
        fs: ["\u05D0\u05D5\u05D4\u05D1\u05EA", "ohevet"],
        mp: ["\u05D0\u05D5\u05D4\u05D1\u05D9\u05DD", "ohavim"],
    };
    const form = ohev[subj.pk];
    if (!form)
        return null;
    const inf = pick(INFINITIVES);
    const partsHe = [subj.he, form[0], inf[0]];
    const partsTr = [subj.tr, form[1], inf[1]];
    let en = `${cap(subj.en)} like${subj.is3sg ? "s" : ""} ${inf[3]}`;
    if (inf[4] === "destination") {
        const d = pick(DESTINATIONS);
        partsHe.push(d[0]);
        partsTr.push(d[1]);
        en += ` ${d[2]}`;
    }
    return sent(partsHe.join(" "), partsTr.join(" "), en);
}
function likeObject() {
    const subj = pick(SUBJECTS);
    const ohev = {
        ms: ["\u05D0\u05D5\u05D4\u05D1", "ohev"],
        fs: ["\u05D0\u05D5\u05D4\u05D1\u05EA", "ohevet"],
        mp: ["\u05D0\u05D5\u05D4\u05D1\u05D9\u05DD", "ohavim"],
    };
    const form = ohev[subj.pk];
    if (!form)
        return null;
    const extras = [
        ["\u05E1\u05D5\u05E9\u05D9", "sushi", "sushi"],
        ["\u05E7\u05E4\u05D4", "kafe", "coffee"],
    ];
    const obj = pick([...FOOD, ...DRINK, ...extras]);
    return sent(`${subj.he} ${form[0]} ${obj[0]}`, `${subj.tr} ${form[1]} ${obj[1]}`, `${cap(subj.en)} like${subj.is3sg ? "s" : ""} ${obj[2]}`);
}
function qWhatPresent() {
    const verbs = VERBS.filter((v) => v.pres &&
        !["about", "about_it", "quote", "location", "country", "destination", "time_or_loc", "person", "person_obj"].includes(v.comp) &&
        !_MODAL_VERBS.has(v.en[0]));
    const v = pick(verbs);
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const en = `What ${enDoes(subj)} ${enLower(subj.en)} ${enBase(v)}?`;
    return sent(`\u05DE\u05D4 ${subj.he} ${vf[0]}?`, `ma ${subj.tr} ${vf[1]}?`, en);
}
function qWhatPast() {
    const verbs = VERBS.filter((v) => v.past &&
        !["about", "about_it", "quote", "location", "country", "destination", "time_or_loc", "person", "person_obj"].includes(v.comp) &&
        !_MODAL_VERBS.has(v.en[0]));
    const v = pick(verbs);
    const pairs = validPastPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const time = pick([...PAST_TIMES, null, null, null]);
    let he = `\u05DE\u05D4 ${subj.he} ${vf[0]}`;
    let tr = `ma ${subj.tr} ${vf[1]}`;
    let en = `What did ${enLower(subj.en)} ${enBase(v)}`;
    if (time) {
        he += ` ${time[0]}`;
        tr += ` ${time[1]}`;
        en += ` ${time[2]}`;
    }
    return sent(he + "?", tr + "?", en + "?");
}
function qWhere() {
    const verbs = VERBS.filter((v) => ["time_or_loc", "location", "country"].includes(v.comp));
    const v = pick(verbs);
    // try present first
    let pairs = validPresentPairs(v);
    if (pairs.length) {
        const [subj, vf] = pick(pairs);
        return sent(`\u05D0\u05D9\u05E4\u05D4 ${subj.he} ${vf[0]}?`, `eifo ${subj.tr} ${vf[1]}?`, `Where ${enDoes(subj)} ${enLower(subj.en)} ${enBase(v)}?`);
    }
    pairs = validPastPairs(v);
    if (pairs.length) {
        const [subj, vf] = pick(pairs);
        return sent(`\u05D0\u05D9\u05E4\u05D4 ${subj.he} ${vf[0]}?`, `eifo ${subj.tr} ${vf[1]}?`, `Where did ${enLower(subj.en)} ${enBase(v)}?`);
    }
    return null;
}
function qWhereTo() {
    const verbs = VERBS.filter((v) => v.comp === "destination");
    const v = pick(verbs);
    let pairs = validPresentPairs(v);
    if (!pairs.length)
        pairs = validPastPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    // Check if this form is from the past tense
    const pastValues = v.past ? Object.values(v.past) : [];
    const isPast = pastValues.some((f) => f[0] === vf[0] && f[1] === vf[1]);
    if (isPast) {
        return sent(`\u05DC\u05D0\u05DF ${subj.he} ${vf[0]}?`, `le'an ${subj.tr} ${vf[1]}?`, `Where did ${enLower(subj.en)} ${enBase(v)} to?`);
    }
    return sent(`\u05DC\u05D0\u05DF ${subj.he} ${vf[0]}?`, `le'an ${subj.tr} ${vf[1]}?`, `Where ${enBe(subj)} ${enLower(subj.en)} ${v.en[4]}?`);
}
function qWhen() {
    const whenNouns = SHEL_NOUNS.filter((n) => n[2] === "flight" || n[2] === "class");
    if (!whenNouns.length)
        return null;
    const noun = pick(whenNouns);
    const shel = pick(SHEL);
    return sent(`\u05DE\u05EA\u05D9 ${noun[0]} ${shel[0]}?`, `matai ${noun[1]} ${shel[1]}?`, `When is ${shel[2]} ${noun[2]}?`);
}
function qWhy() {
    const v = pick(VERBS.filter((v) => v.pres && !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    if (Math.random() < 0.5) {
        // negative
        return sent(`\u05DC\u05DE\u05D4 ${subj.he} \u05DC\u05D0 ${vf[0]} ${comp[0]}?`, `lama ${subj.tr} lo ${vf[1]} ${comp[1]}?`, `Why ${enDoesnt(subj)} ${enLower(subj.en)} ${enBase(v)} ${comp[2]}?`);
    }
    return sent(`\u05DC\u05DE\u05D4 ${subj.he} ${vf[0]} ${comp[0]}?`, `lama ${subj.tr} ${vf[1]} ${comp[1]}?`, `Why ${enDoes(subj)} ${enLower(subj.en)} ${enBase(v)} ${comp[2]}?`);
}
function qHow() {
    const noun = pick(SHEL_NOUNS);
    const shel = pick(SHEL);
    return sent(`\u05D0\u05D9\u05DA ${noun[0]} ${shel[0]}?`, `eikh ${noun[1]} ${shel[1]}?`, `How is ${shel[2]} ${noun[2]}?`);
}
function negationPresent() {
    const v = pick(VERBS.filter((v) => v.pres && v.comp in COMP_MAP && !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} \u05DC\u05D0 ${vf[0]} ${comp[0]}`, `${subj.tr} lo ${vf[1]} ${comp[1]}`, `${cap(subj.en)} ${enDoesnt(subj)} ${enBase(v)} ${comp[2]}`);
}
function negationPast() {
    const v = pick(VERBS.filter((v) => v.past &&
        v.comp !== "about" &&
        v.comp !== "about_it" &&
        !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPastPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    if (Math.random() < 0.4) {
        return sent(`${subj.he} \u05DC\u05D0 ${vf[0]} \u05DB\u05DC\u05D5\u05DD`, `${subj.tr} lo ${vf[1]} klum`, `${cap(subj.en)} didn't ${enBase(v)} anything`);
    }
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} \u05DC\u05D0 ${vf[0]} ${comp[0]}`, `${subj.tr} lo ${vf[1]} ${comp[1]}`, `${cap(subj.en)} didn't ${enBase(v)} ${comp[2]}`);
}
function tooAdj() {
    const adj = pick(MIDI_ADJ);
    return sent(`\u05D6\u05D4 ${adj[0]} \u05DE\u05D3\u05D9`, `ze ${adj[1]} midai`, `It's too ${adj[2]}`);
}
function alreadyPast() {
    const v = pick(VERBS.filter((v) => v.past && v.comp in COMP_MAP && !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPastPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} \u05DB\u05D1\u05E8 ${vf[0]} ${comp[0]}`, `${subj.tr} kvar ${vf[1]} ${comp[1]}`, `${cap(subj.en)} already ${enPast(v)} ${comp[2]}`);
}
function possession() {
    const yl = pick(YESH_L);
    const noun = pick(POSSESSABLE);
    if (Math.random() < 0.5 && POSS_MOD.length) {
        const mod = pick(POSS_MOD);
        return sent(`\u05D9\u05E9 ${yl[0]} ${noun[0]} ${mod[0]}`, `yesh ${yl[1]} ${noun[1]} ${mod[1]}`, `${cap(yl[2])} ${yl[2] === "he" || yl[2] === "she" ? "has" : "have"} a ${mod[2]} ${noun[2]}`);
    }
    return sent(`\u05D9\u05E9 ${yl[0]} ${noun[0]}`, `yesh ${yl[1]} ${noun[1]}`, `${cap(yl[2])} ${yl[2] === "he" || yl[2] === "she" ? "has" : "have"} a ${noun[2]}`);
}
function thinkThat() {
    const subj = pick(SUBJECTS);
    const forms = {
        ms: ["\u05D7\u05D5\u05E9\u05D1", "khoshev"],
        fs: ["\u05D7\u05D5\u05E9\u05D1\u05EA", "khoshevet"],
    };
    const form = forms[subj.pk];
    if (!form)
        return null;
    if (Math.random() < 0.5) {
        return sent(`${subj.he} ${form[0]} \u05E9\u05DB\u05DF`, `${subj.tr} ${form[1]} shakhen`, `${cap(subj.en)} think${subj.is3sg ? "s" : ""} so`);
    }
    return sent(`${subj.he} ${form[0]} \u05E9\u05DC\u05D0`, `${subj.tr} ${form[1]} shelo`, `${cap(subj.en)} ${subj.is3sg ? "doesn't" : "don't"} think so`);
}
function sureThat() {
    const subj = pick(SUBJECTS.filter((s) => s.ppk === "3ms" || s.ppk === "3fs" || s.ppk === "1s"));
    const bt = subj.g === "m"
        ? ["\u05D1\u05D8\u05D5\u05D7", "batuakh"]
        : ["\u05D1\u05D8\u05D5\u05D7\u05D4", "betukha"];
    const cl = pick(_SURE_CLAUSES);
    const be = subj.is3sg ? "'s" : subj.en === "I" ? "'m" : "'re";
    return sent(`${subj.he} ${bt[0]} ${cl[0]}`, `${subj.tr} ${bt[1]} ${cl[1]}`, `${cap(subj.en)}${be} sure ${cl[2]}`);
}
function becauseOf() {
    const subj = pick(SUBJECTS.filter((s) => s.g === "m" && s.pk === "ms"));
    const state = pick(_BECAUSE_STATES);
    const cause = pick(_BECAUSE_CAUSES);
    const be = subj.is3sg ? "'s" : subj.en === "I" ? "'m" : "'re";
    return sent(`${subj.he} ${state[0]} \u05D1\u05D2\u05DC\u05DC ${cause[0]}`, `${subj.tr} ${state[1]} biglal ${cause[1]}`, `${cap(subj.en)}${be} ${state[2]} because of ${cause[2]}`);
}
function neverPres() {
    const v = pick(VERBS.filter((v) => v.pres && v.comp in COMP_MAP && !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} \u05D0\u05E3 \u05E4\u05E2\u05DD \u05DC\u05D0 ${vf[0]} ${comp[0]}`, `${subj.tr} af pa'am lo ${vf[1]} ${comp[1]}`, `${cap(subj.en)} never ${enBase(v)}${subj.is3sg ? "s" : ""} ${comp[2]}`);
}
function notSo() {
    const subj = pick(SUBJECTS.filter((s) => s.pk === "ms" || s.pk === "fs"));
    const opts = [];
    for (const a of PRED_ADJ) {
        if (subj.g === "m" && a[0])
            opts.push([a[0], a[1], a[4]]);
        else if (subj.g === "f" && a[2])
            opts.push([a[2], a[3], a[4]]);
    }
    if (!opts.length)
        return null;
    const adj = pick(opts);
    let enNeg;
    if (subj.is3sg)
        enNeg = "isn't";
    else if (subj.en === "I")
        enNeg = "am not";
    else
        enNeg = "aren't";
    return sent(`${subj.he} \u05DC\u05D0 \u05DB\u05DC \u05DB\u05DA ${adj[0]}`, `${subj.tr} lo kol kakh ${adj[1]}`, `${cap(subj.en)} ${enNeg} so ${adj[2]}`);
}
function temporalPast() {
    const time = pick(PAST_TIMES);
    const v = pick(VERBS.filter((v) => v.past && !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPastPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    let he = `${time[0]} ${subj.he} ${vf[0]}`;
    let tr = `${time[1]} ${subj.tr} ${vf[1]}`;
    let en = `${cap(time[2])} ${enLower(subj.en)} ${enPast(v)}`;
    if (comp) {
        he += ` ${comp[0]}`;
        tr += ` ${comp[1]}`;
        en += ` ${comp[2]}`;
    }
    return sent(he, tr, en);
}
function frequency() {
    const freqComps = new Set(["food", "drink", "activity", "seeable", "buyable", "sendable"]);
    const v = pick(VERBS.filter((v) => v.pres && freqComps.has(v.comp) && !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    const f = pick(_FREQ_COUNTS);
    const p = pick(_FREQ_PERIODS);
    return sent(`${subj.he} ${vf[0]} ${comp[0]} ${f[0]} ${p[0]}`, `${subj.tr} ${vf[1]} ${comp[1]} ${f[1]} ${p[1]}`, `${cap(subj.en)} ${enPres(v, subj)} ${comp[2]} ${f[2]} ${p[2]}`);
}
function defNounPhrase() {
    const np = pick(DEF_NP);
    return sent(`${np[0]} ${np[3]}`, `${np[1]} ${np[4]}`, `The ${np[5]} ${np[2].replace("the ", "")}`);
}
function evenPast() {
    const name = pick(_EVEN_NAMES);
    const verbsOpts = name[3] === "f" ? _EVEN_VERBS_F : _EVEN_VERBS_M;
    const vo = pick(verbsOpts);
    const obj = pick([
        ["\u05E2\u05D1\u05E8\u05D9\u05EA", "ivrit", "Hebrew"],
        null,
        null,
    ]);
    let he = `\u05D0\u05E4\u05D9\u05DC\u05D5 ${name[0]} ${vo[0][0]}`;
    let tr = `afilu ${name[1]} ${vo[0][1]}`;
    let en = `Even ${name[2]} ${vo[1]}`;
    if (obj) {
        he += ` ${obj[0]}`;
        tr += ` ${obj[1]}`;
        en += ` ${obj[2]}`;
    }
    return sent(he, tr, en);
}
function emphatic() {
    const v = pick(VERBS.filter((v) => v.past && !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPastPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const time = pick(TIME_WORDS.slice(0, 2));
    return sent(`${subj.he} \u05DB\u05DF ${vf[0]} ${time[0]}!`, `${subj.tr} ken ${vf[1]} ${time[1]}!`, `${cap(subj.en)} DID ${enBase(v)} ${time[2]}!`);
}
function shelQuestion() {
    const noun = pick(SHEL_NOUNS);
    return sent(`\u05E9\u05DC \u05DE\u05D9 ${noun[0]}?`, `shel mi ${noun[1]}?`, `Whose ${noun[2]} is it?`);
}
function nobodyNothing() {
    const adj = pick(ZE_ADJ);
    const o = pick(_NOBODY_OPENERS);
    return sent(`${o[0]} ${adj[0]}`, `${o[1]} ${adj[1]}`, `${o[2]} ${adj[2]}`);
}
// === NEW TEMPLATES ===
function needInf() {
    const subj = pick(SUBJECTS.filter((s) => s.pk === "ms" || s.pk === "fs"));
    const form = subj.g === "m" ? _NEED_FORMS.ms : _NEED_FORMS.fs;
    const inf = pick(INFINITIVES);
    const partsHe = [subj.he, form[0], inf[0]];
    const partsTr = [subj.tr, form[1], inf[1]];
    let en = `${cap(subj.en)} need${subj.is3sg ? "s" : ""} ${inf[2]}`;
    if (inf[4] === "destination") {
        const d = pick(DESTINATIONS);
        partsHe.push(d[0]);
        partsTr.push(d[1]);
        en += ` ${d[2]}`;
    }
    else if (inf[4] === "location") {
        const loc = pick(LOCATIONS);
        partsHe.push(loc[0]);
        partsTr.push(loc[1]);
        en += ` ${loc[2]}`;
    }
    return sent(partsHe.join(" "), partsTr.join(" "), en);
}
function yesNoQuestion() {
    const v = pick(VERBS.filter((v) => v.pres && !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} ${vf[0]} ${comp[0]}?`, `${subj.tr} ${vf[1]} ${comp[1]}?`, `${cap(enDoes(subj))} ${enLower(subj.en)} ${enBase(v)} ${comp[2]}?`);
}
function feelLike() {
    const fl = pick(_FEEL_LIKE);
    const inf = pick(INFINITIVES);
    const partsHe = [fl[0], inf[0]];
    const partsTr = [fl[1], inf[1]];
    let en = `${cap(fl[2])} feel${fl[2] === "he" || fl[2] === "she" ? "s" : ""} like ${inf[3]}`;
    if (inf[4] === "destination") {
        const d = pick(DESTINATIONS);
        partsHe.push(d[0]);
        partsTr.push(d[1]);
        en += ` ${d[2]}`;
    }
    return sent(partsHe.join(" "), partsTr.join(" "), en);
}
function possibleInf() {
    const inf = pick(_POSSIBLE_COMPS);
    const loc = Math.random() < 0.4 ? pick(LOCATIONS) : null;
    let he = `\u05D0\u05E4\u05E9\u05E8 ${inf[0]}`;
    let tr = `efshar ${inf[1]}`;
    let en = `Is it possible ${inf[2]}`;
    if (loc) {
        he += ` ${loc[0]}`;
        tr += ` ${loc[1]}`;
        en += ` ${loc[2]}`;
    }
    return sent(he + "?", tr + "?", en + "?");
}
function couldBe() {
    const phrase = pick(_COULD_BE);
    return sent(phrase[0], phrase[1], phrase[2]);
}
function qHowMany() {
    const noun = pick(_COUNTABLE);
    const yl = pick(YESH_L);
    return sent(`\u05DB\u05DE\u05D4 ${noun[0]} \u05D9\u05E9 ${yl[0]}?`, `kama ${noun[1]} yesh ${yl[1]}?`, `How many ${noun[2]} ${yl[2] === "he" || yl[2] === "she" ? "does" : "do"} ${enLower(yl[2])} have?`);
}
function qAbout() {
    const topic = pick(_ABOUT_TOPICS);
    const v = pick(VERBS.filter((v) => v.comp === "about" || v.comp === "about_it"));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    return sent(`${topic[0]} ${subj.he} ${vf[0]}?`, `${topic[1]} ${subj.tr} ${vf[1]}?`, `${topic[2]} ${enBe(subj)} ${enLower(subj.en)} ${v.en[4]}?`);
}
function stillPres() {
    const adv = _ADV.still;
    const v = pick(VERBS.filter((v) => v.pres && ["time_or_loc", "location", "country"].includes(v.comp)));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} ${adv[0]} ${vf[0]} ${comp[0]}`, `${subj.tr} ${adv[1]} ${vf[1]} ${comp[1]}`, `${cap(subj.en)} ${adv[2]} ${enPres(v, subj)} ${comp[2]}`);
}
function stillAdj() {
    const adv = _ADV.still;
    const subj = pick(SUBJECTS.filter((s) => s.pk === "ms" || s.pk === "fs"));
    const adj = getPredAdj(subj);
    if (!adj)
        return null;
    return sent(`${subj.he} ${adv[0]} ${adj[0]}`, `${subj.tr} ${adv[1]} ${adj[1]}`, `${cap(subj.en)}${enBe(subj, true)} ${adv[2]} ${adj[2]}`);
}
function almostPast() {
    const adv = _ADV.almost;
    const v = pick(VERBS.filter((v) => v.past && v.comp in COMP_MAP));
    const pairs = validPastPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} ${adv[0]} ${vf[0]} ${comp[0]}`, `${subj.tr} ${adv[1]} ${vf[1]} ${comp[1]}`, `${cap(subj.en)} ${adv[2]} ${enPast(v)} ${comp[2]}`);
}
function againMore() {
    const adv = _ADV.again;
    const v = pick(VERBS.filter((v) => v.pres && (v.comp === "food" || v.comp === "drink")));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} ${vf[0]} ${adv[0]} ${comp[0]}`, `${subj.tr} ${vf[1]} ${adv[1]} ${comp[1]}`, `${cap(subj.en)} ${enPres(v, subj)} more ${comp[2]}`);
}
function whenClause() {
    const v1 = pick(VERBS.filter((v) => v.past && !_MODAL_VERBS.has(v.en[0])));
    const v2 = pick(VERBS.filter((v) => v.past && v !== v1 && !_MODAL_VERBS.has(v.en[0])));
    const pairs1 = validPastPairs(v1);
    const pairs2 = validPastPairs(v2);
    if (!pairs1.length || !pairs2.length)
        return null;
    const [subj1, vf1] = pick(pairs1);
    const [subj2, vf2] = pick(pairs2);
    const comp1 = getComp(v1, subj1);
    const comp2 = getComp(v2, subj2);
    let he = `\u05DB\u05E9${subj1.he} ${vf1[0]}`;
    let tr = `kshe${subj1.tr} ${vf1[1]}`;
    let en = `When ${enLower(subj1.en)} ${enPast(v1)}`;
    if (comp1) {
        he += ` ${comp1[0]}`;
        tr += ` ${comp1[1]}`;
        en += ` ${comp1[2]}`;
    }
    he += `, ${subj2.he} ${vf2[0]}`;
    tr += `, ${subj2.tr} ${vf2[1]}`;
    en += `, ${enLower(subj2.en)} ${enPast(v2)}`;
    if (comp2) {
        he += ` ${comp2[0]}`;
        tr += ` ${comp2[1]}`;
        en += ` ${comp2[2]}`;
    }
    return sent(he, tr, en);
}
function alwaysPres() {
    const adv = _ADV.always;
    const v = pick(VERBS.filter((v) => v.pres && v.comp in COMP_MAP && !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} ${adv[0]} ${vf[0]} ${comp[0]}`, `${subj.tr} ${adv[1]} ${vf[1]} ${comp[1]}`, `${cap(subj.en)} ${adv[2]} ${enPres(v, subj)} ${comp[2]}`);
}
function sometimesPres() {
    const adv = _ADV.sometimes;
    const v = pick(VERBS.filter((v) => v.pres && v.comp in COMP_MAP && !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} ${adv[0]} ${vf[0]} ${comp[0]}`, `${subj.tr} ${adv[1]} ${vf[1]} ${comp[1]}`, `${cap(subj.en)} ${adv[2]} ${enPres(v, subj)} ${comp[2]}`);
}
function onlyObject() {
    const adv = _ADV.only;
    const v = pick(VERBS.filter((v) => v.pres && (v.comp === "food" || v.comp === "drink")));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    const comp = getComp(v, subj);
    if (!comp)
        return null;
    return sent(`${subj.he} ${vf[0]} ${adv[0]} ${comp[0]}`, `${subj.tr} ${vf[1]} ${adv[1]} ${comp[1]}`, `${cap(subj.en)} ${adv[2]} ${enPres(v, subj)} ${comp[2]}`);
}
function aLotPres() {
    const adv = _ADV.a_lot;
    const v = pick(VERBS.filter((v) => v.pres &&
        (v.comp === "time_or_loc" || v.comp === "activity") &&
        !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPresentPairs(v);
    if (!pairs.length)
        return null;
    const [subj, vf] = pick(pairs);
    return sent(`${subj.he} ${vf[0]} ${adv[0]}`, `${subj.tr} ${vf[1]} ${adv[1]}`, `${cap(subj.en)} ${enPres(v, subj)} ${adv[2]}`);
}
function togetherPast() {
    const adv = _ADV.together;
    const v = pick(VERBS.filter((v) => v.past && !_MODAL_VERBS.has(v.en[0])));
    const pairs = validPastPairs(v);
    if (!pairs.length)
        return null;
    // "together" only makes sense with plural subjects
    const plural = pairs.filter(([s]) => s.pk === "mp" || s.en === "we" || s.en === "they");
    if (!plural.length)
        return null;
    const [subj, vf] = pick(plural);
    const comp = getComp(v, subj);
    let he = `${subj.he} ${vf[0]}`;
    let tr = `${subj.tr} ${vf[1]}`;
    let en = `${cap(subj.en)} ${enPast(v)}`;
    if (comp) {
        he += ` ${comp[0]}`;
        tr += ` ${comp[1]}`;
        en += ` ${comp[2]}`;
    }
    he += ` ${adv[0]}`;
    tr += ` ${adv[1]}`;
    en += ` ${adv[2]}`;
    return sent(he, tr, en);
}
function fixedExpression() {
    const expr = pick(_FIXED);
    return sent(expr[0], expr[1], expr[2]);
}
// === MAIN ===
const TEMPLATES = [
    [presentWithObject, 10, "present, direct object"],
    [presentIntransitive, 6, "present, location"],
    [pastWithObject, 10, "past, direct object"],
    [pastIntransitive, 5, "past, location"],
    [pastDirection, 6, "past, direction"],
    [nominalAdj, 6, "adjective"],
    [nominalZe, 4, "\u05D6\u05D4, adjective"],
    [nominalLocation, 4, "location"],
    [pastHaya, 5, "past \u05D4\u05D9\u05D4, adjective"],
    [zeHaya, 4, "past \u05D4\u05D9\u05D4"],
    [wantInf, 8, "\u05E8\u05D5\u05E6\u05D4, infinitive"],
    [canInf, 6, "\u05D9\u05DB\u05D5\u05DC, infinitive"],
    [likeInf, 6, "\u05D0\u05D5\u05D4\u05D1, infinitive"],
    [likeObject, 5, "\u05D0\u05D5\u05D4\u05D1, object"],
    [qWhatPresent, 7, "\u05DE\u05D4 question, present"],
    [qWhatPast, 6, "\u05DE\u05D4 question, past"],
    [qWhere, 5, "\u05D0\u05D9\u05E4\u05D4 question"],
    [qWhereTo, 4, "\u05DC\u05D0\u05DF question"],
    [qWhen, 3, "\u05DE\u05EA\u05D9 question, \u05E9\u05DC"],
    [qWhy, 5, "\u05DC\u05DE\u05D4 question"],
    [qHow, 3, "\u05D0\u05D9\u05DA question, \u05E9\u05DC"],
    [negationPresent, 7, "negation, present"],
    [negationPast, 5, "negation, past"],
    [tooAdj, 4, "\u05DE\u05D3\u05D9, adjective"],
    [alreadyPast, 5, "\u05DB\u05D1\u05E8, past"],
    [possession, 5, "\u05D9\u05E9 \u05DC, possession"],
    [thinkThat, 4, "\u05D7\u05D5\u05E9\u05D1 \u05E9, clause"],
    [sureThat, 3, "\u05D1\u05D8\u05D5\u05D7 \u05E9, clause"],
    [becauseOf, 3, "\u05D1\u05D2\u05DC\u05DC, clause"],
    [neverPres, 4, "\u05D0\u05E3 \u05E4\u05E2\u05DD, negation"],
    [notSo, 4, "\u05DC\u05D0 \u05DB\u05DC \u05DB\u05DA, adjective"],
    [temporalPast, 5, "time, past"],
    [frequency, 4, "frequency, present"],
    [defNounPhrase, 3, "definite, adjective"],
    [evenPast, 3, "\u05D0\u05E4\u05D9\u05DC\u05D5, past"],
    [emphatic, 3, "\u05DB\u05DF emphatic, past"],
    [shelQuestion, 3, "\u05E9\u05DC \u05DE\u05D9 question"],
    [nobodyNothing, 3, "\u05D0\u05E3 \u05D0\u05D7\u05D3 / \u05E9\u05D5\u05DD \u05D3\u05D1\u05E8"],
    [needInf, 7, "\u05E6\u05E8\u05D9\u05DA, infinitive"],
    [yesNoQuestion, 6, "yes/no question"],
    [feelLike, 5, "\u05D1\u05D0 \u05DC, infinitive"],
    [possibleInf, 3, "\u05D0\u05E4\u05E9\u05E8, infinitive"],
    [couldBe, 2, "\u05D9\u05DB\u05D5\u05DC \u05DC\u05D4\u05D9\u05D5\u05EA"],
    [qHowMany, 4, "\u05DB\u05DE\u05D4 question, \u05D9\u05E9 \u05DC"],
    [qAbout, 3, "\u05E2\u05DC \u05DE\u05D4/\u05DE\u05D9 question"],
    [stillPres, 4, "\u05E2\u05D3\u05D9\u05D9\u05DF, present"],
    [stillAdj, 3, "\u05E2\u05D3\u05D9\u05D9\u05DF, adjective"],
    [almostPast, 4, "\u05DB\u05DE\u05E2\u05D8, past"],
    [againMore, 3, "\u05E2\u05D5\u05D3, present"],
    [whenClause, 4, "\u05DB\u05E9 clause, past"],
    [alwaysPres, 5, "\u05EA\u05DE\u05D9\u05D3, present"],
    [sometimesPres, 4, "\u05DC\u05E4\u05E2\u05DE\u05D9\u05DD, present"],
    [onlyObject, 3, "\u05E8\u05E7, present"],
    [aLotPres, 3, "\u05D4\u05E8\u05D1\u05D4, present"],
    [togetherPast, 3, "\u05D9\u05D7\u05D3, past"],
    [fixedExpression, 3, "expression"],
];
const _funcs = TEMPLATES.map((e) => e[0]);
const _weights = TEMPLATES.map((e) => e[1]);
const _tags = TEMPLATES.map((e) => e[2]);
/**
 * Generate one random sentence. Retries up to 20 times on null.
 */
export function generate() {
    for (let attempt = 0; attempt < 20; attempt++) {
        const idx = weightedIndex(_weights);
        const result = _funcs[idx]();
        if (result) {
            result.tag = _tags[idx];
            return result;
        }
    }
    // fallback
    return {
        hebrew: "\u05D1\u05D3\u05E8\u05DA \u05DB\u05DC\u05DC",
        transliteration: "baderekh klal",
        english: "Usually",
        tag: "expression",
    };
}
/**
 * Generate a batch of sentences. Draws from the curated pool first;
 * falls back to live generation once the pool is exhausted.
 */
export function generateBatch(n = 20) {
    const results = [];
    while (results.length < n) {
        if (_curatedIndex < _curatedPool.length) {
            results.push(_curatedPool[_curatedIndex++]);
        }
        else {
            results.push(generate());
        }
    }
    return results;
}
