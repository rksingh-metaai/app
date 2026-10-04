#!/usr/bin/env python3
"""Generate Hinglish (romanised Hindi) vocabulary and predictions from
grammar templates.

No commercially usable Hinglish corpus exists, so predictions are built from
Hindi grammar instead: verb forms (kar raha hai, kar liya, karunga),
pronouns with postpositions (mere liye, aapke saath), question words and
everyday chat expressions. Frequencies are hand-assigned tiers on the AOSP
0-255 scale.

Outputs (committed; rerun after editing this file):
  data/hinglish_vocab.txt     every word used below
  data/hinglish_bigrams.txt   "w1 w2 f"
  data/hinglish_trigrams.txt  "w1 w2 w3 f"
"""

from __future__ import annotations

from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"

# stem, past (masc.), infinitive, imperative (tum), polite (aap),
# future 1st person masc./fem., future 3rd person, future plural/aap
VERBS = [
    ("kar", "kiya", "karna", "karo", "kijiye", "karunga", "karungi", "karega", "karenge"),
    ("ja", "gaya", "jana", "jao", "jaiye", "jaunga", "jaungi", "jayega", "jayenge"),
    ("aa", "aaya", "aana", "aao", "aaiye", "aaunga", "aaungi", "aayega", "aayenge"),
    ("kha", "khaya", "khana", "khao", "khaiye", "khaunga", "khaungi", "khayega", "khayenge"),
    ("pee", "piya", "peena", "piyo", "pijiye", "piyunga", "piyungi", "piyega", "piyenge"),
    ("so", "soya", "sona", "so jao", "soiye", "sounga", "soungi", "soyega", "soyenge"),
    ("dekh", "dekha", "dekhna", "dekho", "dekhiye", "dekhunga", "dekhungi", "dekhega", "dekhenge"),
    ("sun", "suna", "sunna", "suno", "suniye", "sununga", "sunungi", "sunega", "sunenge"),
    ("bol", "bola", "bolna", "bolo", "boliye", "bolunga", "bolungi", "bolega", "bolenge"),
    ("padh", "padha", "padhna", "padho", "padhiye", "padhunga", "padhungi", "padhega", "padhenge"),
    ("likh", "likha", "likhna", "likho", "likhiye", "likhunga", "likhungi", "likhega", "likhenge"),
    ("soch", "socha", "sochna", "socho", "sochiye", "sochunga", "sochungi", "sochega", "sochenge"),
    ("chal", "chala", "chalna", "chalo", "chaliye", "chalunga", "chalungi", "chalega", "chalenge"),
    ("ruk", "ruka", "rukna", "ruko", "rukiye", "rukunga", "rukungi", "rukega", "rukenge"),
    ("baith", "baitha", "baithna", "baitho", "baithiye", "baithunga", "baithungi", "baithega", "baithenge"),
    ("mil", "mila", "milna", "milo", "miliye", "milunga", "milungi", "milega", "milenge"),
    ("de", "diya", "dena", "do", "dijiye", "dunga", "dungi", "dega", "denge"),
    ("le", "liya", "lena", "lo", "lijiye", "lunga", "lungi", "lega", "lenge"),
    ("bhej", "bheja", "bhejna", "bhejo", "bhejiye", "bhejunga", "bhejungi", "bhejega", "bhejenge"),
    ("bata", "bataya", "batana", "batao", "bataiye", "bataunga", "bataungi", "batayega", "batayenge"),
    ("samajh", "samjha", "samajhna", "samjho", "samjhiye", "samjhunga", "samjhungi", "samjhega", "samjhenge"),
    ("khel", "khela", "khelna", "khelo", "kheliye", "khelunga", "khelungi", "khelega", "khelenge"),
    ("rakh", "rakha", "rakhna", "rakho", "rakhiye", "rakhunga", "rakhungi", "rakhega", "rakhenge"),
    ("puch", "pucha", "puchna", "pucho", "puchiye", "puchunga", "puchungi", "puchega", "puchenge"),
    ("sikh", "sikha", "sikhna", "sikho", "sikhiye", "sikhunga", "sikhungi", "sikhega", "sikhenge"),
    ("bana", "banaya", "banana", "banao", "banaiye", "banaunga", "banaungi", "banayega", "banayenge"),
    ("chhod", "chhoda", "chhodna", "chhodo", "chhodiye", "chhodunga", "chhodungi", "chhodega", "chhodenge"),
    ("nikal", "nikla", "nikalna", "niklo", "nikaliye", "niklunga", "niklungi", "niklega", "niklenge"),
    ("pahunch", "pahuncha", "pahunchna", "pahuncho", "pahunchiye", "pahunchunga", "pahunchungi", "pahunchega", "pahunchenge"),
    ("ghoom", "ghooma", "ghoomna", "ghoomo", "ghoomiye", "ghoomunga", "ghoomungi", "ghoomega", "ghoomenge"),
    ("khareed", "khareeda", "khareedna", "khareedo", "khareediye", "khareedunga", "khareedungi", "khareedega", "khareedenge"),
    ("bula", "bulaya", "bulana", "bulao", "bulaiye", "bulaunga", "bulaungi", "bulayega", "bulayenge"),
    ("dhoondh", "dhoondha", "dhoondhna", "dhoondho", "dhoondhiye", "dhoondhunga", "dhoondhungi", "dhoondhega", "dhoondhenge"),
    ("utha", "uthaya", "uthana", "uthao", "uthaiye", "uthaunga", "uthaungi", "uthayega", "uthayenge"),
    ("pakad", "pakda", "pakadna", "pakdo", "pakadiye", "pakdunga", "pakdungi", "pakdega", "pakdenge"),
    ("jeet", "jeeta", "jeetna", "jeeto", "jeetiye", "jeetunga", "jeetungi", "jeetega", "jeetenge"),
    ("haar", "haara", "haarna", "haaro", "haariye", "haarunga", "haarungi", "haarega", "haarenge"),
    ("ro", "roya", "rona", "ro mat", "roiye", "rounga", "roungi", "royega", "royenge"),
    ("has", "hasa", "hasna", "haso", "hasiye", "hasunga", "hasungi", "hasega", "hasenge"),
    ("lag", "laga", "lagna", "lago", "lagiye", "lagunga", "lagungi", "lagega", "lagenge"),
]
# The most used verbs get higher frequencies.
TOP_VERBS = {"kar", "ja", "aa", "kha", "dekh", "bol", "mil", "de", "le", "bata", "chal", "so"}

PRONOUN_SUBJECTS = {  # subject -> continuous form, copula
    "main": ("raha", "hoon"), "mai": ("raha", "hoon"), "hum": ("rahe", "hain"),
    "tum": ("rahe", "ho"), "aap": ("rahe", "ho"), "woh": ("raha", "hai"),
    "wo": ("raha", "hai"), "ye": ("raha", "hai"), "yeh": ("raha", "hai"),
}
POSSESSIVES = ["mera", "meri", "mere", "tera", "teri", "tere", "tumhara",
               "tumhari", "tumhare", "aapka", "aapki", "aapke", "hamara",
               "hamari", "hamare", "uska", "uski", "uske", "unka", "unki", "unke"]
OBLIQUE = ["mere", "tere", "tumhare", "aapke", "hamare", "uske", "unke", "iske"]
POSTPOSITIONS = ["liye", "saath", "paas", "baare", "ghar"]
NOUNS_AFTER_POSSESSIVE = ["ghar", "naam", "dost", "bhai", "papa", "mummy", "kaam",
                          "phone", "number", "paas", "liye", "saath"]

# Hand-picked everyday chat pairs: first -> [(next, f), ...]
CHAT_BIGRAMS = {
    "kya": [("hua", 225), ("hai", 225), ("kar", 215), ("baat", 210), ("haal", 205),
            ("scene", 190), ("plan", 190), ("kiya", 195), ("bol", 185), ("matlab", 190)],
    "kaise": [("ho", 230), ("hai", 210), ("hain", 205), ("kiya", 190), ("pata", 180)],
    "kahan": [("ho", 225), ("hai", 210), ("ja", 205), ("gaye", 200), ("se", 195)],
    "kab": [("aa", 215), ("aaoge", 210), ("milenge", 205), ("tak", 205), ("hai", 195)],
    "kyun": [("nahi", 210), ("kiya", 200), ("hua", 195), ("bhai", 180)],
    "kitna": [("hai", 210), ("time", 195), ("paisa", 185), ("hua", 185)],
    "kaun": [("hai", 220), ("tha", 195), ("aaya", 190), ("bola", 180)],
    "nahi": [("hai", 220), ("pata", 215), ("hoon", 200), ("hua", 200), ("yaar", 200),
             ("chahiye", 195), ("aaya", 190), ("kiya", 190), ("ho", 185), ("toh", 185)],
    "mat": [("karo", 215), ("jao", 200), ("bolo", 200), ("socho", 190), ("ro", 180)],
    "haan": [("ji", 215), ("bhai", 200), ("yaar", 195), ("haan", 190), ("theek", 185)],
    "theek": [("hai", 240), ("hoon", 215), ("ho", 200), ("se", 190)],
    "accha": [("hai", 220), ("laga", 205), ("ji", 200), ("theek", 195), ("hua", 195), ("chalo", 190)],
    "bahut": [("accha", 220), ("badhiya", 210), ("zyada", 205), ("time", 200), ("kuch", 195),
              ("pyaar", 190), ("mushkil", 185)],
    "koi": [("baat", 230), ("nahi", 215), ("problem", 200), ("bhi", 195)],
    "sab": [("theek", 225), ("log", 205), ("kuch", 205), ("ko", 195), ("se", 190)],
    "kuch": [("nahi", 220), ("bhi", 210), ("khaas", 195), ("kaam", 190), ("aur", 185)],
    "pata": [("nahi", 235), ("hai", 215), ("chala", 205), ("tha", 190)],
    "chalo": [("theek", 205), ("bye", 210), ("koi", 195), ("phir", 195), ("milte", 200), ("kal", 190)],
    "arre": [("yaar", 220), ("bhai", 210), ("wah", 190), ("nahi", 185)],
    "yaar": [("kya", 200), ("tum", 190), ("main", 185), ("bas", 180)],
    "bhai": [("kya", 205), ("log", 190), ("tu", 185), ("sahab", 180)],
    "aur": [("kya", 215), ("batao", 210), ("sunao", 205), ("bata", 195), ("haan", 185)],
    "toh": [("kya", 210), ("phir", 205), ("chalo", 195), ("theek", 190)],
    "phir": [("milte", 215), ("se", 205), ("kya", 200), ("bhi", 195)],
    "bas": [("aise", 205), ("yaar", 200), ("ho", 195), ("kar", 195), ("thoda", 185)],
    "kal": [("milte", 225), ("aana", 200), ("subah", 200), ("raat", 195), ("office", 190), ("se", 190)],
    "aaj": [("kya", 210), ("raat", 200), ("subah", 195), ("bahut", 190), ("kal", 185)],
    "abhi": [("aa", 210), ("ja", 200), ("nahi", 205), ("tak", 205), ("kar", 195)],
    "mujhe": [("pata", 220), ("nahi", 215), ("bhi", 200), ("lagta", 200), ("chahiye", 200),
              ("bhook", 185), ("bata", 190)],
    "tujhe": [("pata", 210), ("kya", 200), ("bhi", 190)],
    "aapko": [("pata", 210), ("kya", 200), ("bhi", 190)],
    "kitne": [("baje", 215), ("din", 195), ("log", 190)],
    "ghar": [("pe", 215), ("se", 205), ("ja", 205), ("aa", 200), ("mein", 195), ("wale", 190)],
    "khana": [("kha", 220), ("khaya", 210), ("bana", 195)],
    "good": [("morning", 220), ("night", 210)],
    "shubh": [("ratri", 200), ("prabhat", 195), ("deepawali", 195)],
    "happy": [("Diwali", 220), ("Holi", 210)],
    "ho": [("gaya", 215), ("jayega", 205), ("raha", 210), ("sakta", 200), ("toh", 195)],
    "hai": [("na", 215), ("kya", 210), ("yaar", 200), ("bhai", 190), ("ki", 190)],
    "chahiye": [("tha", 200), ("kya", 195)],
    "lagta": [("hai", 225)],
    "milte": [("hain", 235)],
    "baad": [("mein", 225)],
    "pehle": [("se", 200)],
    "thoda": [("sa", 205), ("time", 200), ("wait", 195)],
}
CHAT_TRIGRAMS = [
    ("kya", "kar", "rahe", 235), ("kar", "rahe", "ho", 235), ("kya", "ho", "raha", 225),
    ("ho", "raha", "hai", 235), ("kaise", "ho", "aap", 215), ("kaise", "ho", "yaar", 205),
    ("kaise", "ho", "bhai", 200), ("main", "theek", "hoon", 225), ("theek", "hai", "na", 205),
    ("theek", "hai", "yaar", 195), ("koi", "baat", "nahi", 240), ("kal", "milte", "hain", 235),
    ("phir", "milte", "hain", 230), ("chalo", "kal", "milte", 200), ("chalo", "phir", "milte", 200),
    ("mujhe", "nahi", "pata", 220), ("mujhe", "pata", "hai", 210), ("pata", "nahi", "yaar", 200),
    ("pata", "nahi", "kya", 195), ("kya", "hua", "yaar", 195), ("kya", "hua", "bhai", 190),
    ("kahan", "ho", "tum", 215), ("kahan", "ho", "aap", 205), ("kab", "aa", "rahe", 205),
    ("aa", "rahe", "ho", 220), ("ja", "rahe", "ho", 215), ("bahut", "accha", "hai", 215),
    ("sab", "theek", "hai", 230), ("ghar", "pe", "hoon", 200), ("ghar", "aa", "jao", 195),
    ("khana", "kha", "liya", 210), ("khana", "khaya", "kya", 200), ("kitne", "baje", "aaoge", 195),
    ("aur", "kya", "chal", 200), ("kya", "chal", "raha", 215), ("chal", "raha", "hai", 220),
    ("kuch", "nahi", "yaar", 200), ("nahi", "pata", "yaar", 190), ("haan", "theek", "hai", 200),
    ("accha", "theek", "hai", 205), ("baad", "mein", "baat", 205), ("mein", "baat", "karte", 200),
    ("baat", "karte", "hain", 210), ("kya", "baat", "hai", 220), ("arre", "yaar", "kya", 195),
    ("good", "morning", "ji", 190), ("happy", "Diwali", "to", 220), ("Diwali", "to", "you", 220),
    ("happy", "Holi", "to", 210), ("Holi", "to", "you", 210), ("Eid", "Mubarak", "to", 200),
    ("Mubarak", "to", "you", 200), ("happy", "birthday", "to", 240), ("birthday", "to", "you", 240),
    ("wish", "you", "a", 230), ("you", "a", "very", 210), ("a", "very", "happy", 220),
    ("please", "do", "the", 190), ("do", "the", "needful", 210), ("kindly", "do", "the", 190),
    ("revert", "back", "to", 180),
]

# Places / things typed with postpositions and motion verbs.
PLACES = ["ghar", "office", "school", "college", "market", "bazaar", "station",
          "hospital", "mandir", "dukaan", "bank", "gaon", "shehar", "kamre",
          "gaadi", "bus", "train", "metro"]
POSTPOSITION_AFTER_PLACE = [("pe", 205), ("se", 200), ("mein", 200), ("ja", 195),
                            ("aa", 190), ("tak", 180), ("ke", 175)]
ADJECTIVES = ["accha", "badhiya", "sahi", "galat", "bura", "mast", "zabardast",
              "mushkil", "aasan", "sasta", "mehnga", "bada", "chhota", "naya",
              "purana", "khatarnak", "pyaara", "sundar", "zaroori", "theek"]
INTENSIFIERS = [("bahut", 210), ("bohot", 200), ("kaafi", 190), ("thoda", 185),
                ("ekdum", 185), ("itna", 180), ("bilkul", 180)]
TIME_WORDS = ["aaj", "kal", "parso", "abhi", "subah", "shaam", "raat", "dopahar"]
# Extra everyday pairs.
MORE_BIGRAMS = {
    "kitne": [("ka", 205), ("ki", 200), ("paise", 195)],
    "paise": [("de", 200), ("bhej", 195), ("nahi", 195), ("hai", 190)],
    "mummy": [("papa", 205), ("ne", 200), ("ko", 195)],
    "papa": [("ne", 200), ("ko", 195), ("ka", 190)],
    "khush": [("raho", 205), ("hai", 200), ("hoon", 195)],
    "dhyan": [("rakhna", 215), ("se", 205), ("do", 195)],
    "apna": [("dhyan", 215), ("kaam", 200), ("ghar", 195)],
    "shukriya": [("bhai", 200), ("ji", 195), ("dost", 190)],
    "dhanyavaad": [("ji", 200), ("aapka", 195)],
    "jaldi": [("aao", 210), ("se", 205), ("karo", 205), ("batao", 200)],
    "der": [("ho", 210), ("se", 200), ("lagegi", 195)],
    "baat": [("karte", 215), ("karo", 210), ("hui", 205), ("nahi", 200), ("hai", 200)],
    "call": [("karo", 215), ("kar", 210), ("karna", 205), ("kiya", 200)],
    "message": [("karo", 210), ("kar", 205), ("bhej", 200), ("kiya", 195)],
    "photo": [("bhejo", 210), ("bhej", 205), ("dekhi", 195)],
    "time": [("pe", 205), ("nahi", 205), ("hai", 200), ("kya", 195)],
    "khatam": [("ho", 215), ("karo", 205), ("kar", 200)],
    "shuru": [("ho", 210), ("karo", 205), ("kar", 200)],
    "intezaar": [("karo", 210), ("kar", 205)],
    "yaad": [("hai", 210), ("aa", 205), ("rakhna", 200), ("aaya", 195)],
    "pasand": [("hai", 215), ("aaya", 210), ("nahi", 200)],
    "maza": [("aaya", 220), ("aa", 205)],
    "bhook": [("lagi", 215), ("lag", 205)],
    "neend": [("aa", 210), ("nahi", 200)],
    "tabiyat": [("theek", 215), ("kaisi", 210), ("kharab", 205)],
    "kharab": [("hai", 205), ("ho", 200)],
}
MORE_TRIGRAMS = [
    ("apna", "dhyan", "rakhna", 230), ("dhyan", "se", "jana", 205),
    ("khush", "raho", "hamesha", 190), ("baat", "karte", "hain", 215),
    ("call", "karna", "mujhe", 200), ("mujhe", "call", "karna", 205),
    ("photo", "bhej", "do", 205), ("jaldi", "se", "aao", 200),
    ("maza", "aa", "gaya", 220), ("bhook", "lagi", "hai", 210),
    ("neend", "aa", "rahi", 205), ("aa", "rahi", "hai", 215),
    ("tabiyat", "kaisi", "hai", 210), ("tabiyat", "theek", "hai", 210),
    ("pasand", "aaya", "kya", 195), ("yaad", "aa", "rahi", 200),
    ("der", "ho", "gayi", 210), ("ho", "gayi", "hai", 205),
    ("khatam", "ho", "gaya", 210), ("ho", "gaya", "hai", 215),
    ("kitne", "ka", "hai", 205), ("paise", "bhej", "do", 205),
    ("time", "pe", "aana", 195), ("time", "nahi", "hai", 200),
]
# Common alternative spellings: every phrase containing the key is also
# emitted with each variant (slightly lower frequency).
VARIANTS = {
    "nahi": ["nhi", "nahin", "nai"], "accha": ["acha", "achha"], "kyun": ["kyu", "kyon"],
    "hain": ["hai"], "theek": ["thik"], "bahut": ["bohot", "bahot"],
    "kya": ["kia"], "main": ["mai"], "mujhe": ["muje"], "kuch": ["kuchh"],
    "phir": ["fir"], "yaar": ["yar"], "zyada": ["jyada"], "kaise": ["kese"],
    "raha": ["rha"], "rahi": ["rhi"], "rahe": ["rhe"], "haan": ["han"],
    "abhi": ["abi"], "toh": ["to"], "kar": ["kr"], "karo": ["kro"], "karna": ["krna"], "woh": ["wo"], "yeh": ["ye"],
}
VARIANT_PENALTY = 15


def main() -> None:
    bigrams: dict[tuple[str, str], int] = {}
    trigrams: dict[tuple[str, str, str], int] = {}
    vocab: set[str] = set()

    def bi(a: str, b: str, f: int) -> None:
        bigrams[(a, b)] = max(bigrams.get((a, b), 0), f)

    def tri(a: str, b: str, c: str, f: int) -> None:
        trigrams[(a, b, c)] = max(trigrams.get((a, b, c), 0), f)

    # Continuous / perfect aspect and copulas.
    for cont, copulas in (("raha", ["hai", "hoon", "tha", "ho"]),
                          ("rahi", ["hai", "hoon", "thi", "ho"]),
                          ("rahe", ["ho", "hain", "the", "hai"])):
        for i, cop in enumerate(copulas):
            bi(cont, cop, 225 - 10 * i)

    for stem, past, inf, imp, polite, fut1m, fut1f, fut3, futpl in VERBS:
        top = stem in TOP_VERBS
        base = 215 if top else 185
        words = [stem, past, inf, polite, fut1m, fut1f, fut3, futpl, *imp.split()]
        vocab.update(words)
        # kar raha / kar rahi / kar rahe; kar liya / kar diya; kar lo / kar do
        for i, cont in enumerate(("raha", "rahi", "rahe")):
            bi(stem, cont, base - 5 * i)
        for i, (aux, f) in enumerate((("liya", base - 10), ("diya", base - 15),
                                      ("lo", base - 15), ("do", base - 20),
                                      ("sakta", base - 20), ("chuka", base - 30))):
            if aux != stem:
                bi(stem, aux, f)
        # past: kiya hai / gaya tha; infinitive: karna hai / karna tha / karna chahiye
        for i, nxt in enumerate(("hai", "tha", "kya")):
            bi(past, nxt, base - 15 - 10 * i)
        for i, nxt in enumerate(("hai", "tha", "chahiye", "padega", "nahi")):
            bi(inf, nxt, base - 15 - 8 * i)
        # main kar raha hoon / tum kar rahe ho / woh kar raha hai
        for subj, (cont, cop) in PRONOUN_SUBJECTS.items():
            tri(subj, stem, cont, base - 15)
            tri(stem, cont, cop, base)
        for cont, cops in (("raha", ("hai", "hoon", "tha")), ("rahi", ("hai", "hoon", "thi")),
                           ("rahe", ("ho", "hain", "the"))):
            for i, cop in enumerate(cops):
                tri(stem, cont, cop, base - 5 - 10 * i)
        tri("kya", stem, "rahe", base - 10)
        tri("kya", stem, "raha", base - 15)
        tri(stem, "liya", "kya", base - 25)
        tri(stem, "diya", "hai", base - 25)
        tri("nahi", inf, "hai", base - 25)
        tri("mujhe", inf, "hai", base - 20)

    for subj, (cont, cop) in PRONOUN_SUBJECTS.items():
        vocab.add(subj)
        for i, nxt in enumerate(("bhi", "toh", "theek", "abhi", "kal", "ghar", "nahi")):
            bi(subj, nxt, 200 - 5 * i)
        tri(subj, "theek", cop, 205)

    for pos in POSSESSIVES:
        vocab.add(pos)
        for i, noun in enumerate(NOUNS_AFTER_POSSESSIVE):
            bi(pos, noun, 195 - 3 * i)
    for obl in OBLIQUE:
        vocab.add(obl)
        for i, post in enumerate(POSTPOSITIONS):
            bi(obl, post, 210 - 5 * i)
        tri(obl, "liye", "kuch", 185)
        tri(obl, "saath", "chal", 180)

    for place in PLACES:
        vocab.add(place)
        for post, f in POSTPOSITION_AFTER_PLACE:
            bi(place, post, f)
        tri(place, "ja", "raha", 195)
        tri(place, "pe", "hoon", 195)
        tri(place, "se", "aa", 190)
        tri(place, "pahunch", "gaya", 190)
    for adj in ADJECTIVES:
        vocab.add(adj)
        bi(adj, "hai", 210)
        bi(adj, "laga", 195)
        for inten, f in INTENSIFIERS:
            bi(inten, adj, f - 5)
            tri(inten, adj, "hai", f)
    for t in TIME_WORDS:
        vocab.add(t)
        for nxt, f in (("tak", 195), ("se", 195), ("kya", 190), ("milte", 190), ("aana", 185)):
            bi(t, nxt, f)
    for first, nexts in MORE_BIGRAMS.items():
        for nxt, f in nexts:
            bi(first, nxt, f)
    for a, b, c, f in MORE_TRIGRAMS:
        tri(a, b, c, f)

    for first, nexts in CHAT_BIGRAMS.items():
        for nxt, f in nexts:
            bi(first, nxt, f)
    for a, b, c, f in CHAT_TRIGRAMS:
        tri(a, b, c, f)

    # Spelling variants of every Hinglish phrase.
    def variants(words: tuple[str, ...]) -> list[tuple[str, ...]]:
        out = [words]
        for i, w in enumerate(words):
            for alt in VARIANTS.get(w, ()):
                out += [v[:i] + (alt,) + v[i + 1:] for v in list(out) if v[i] == w]
        return out[1:]

    for (a, b), f in list(bigrams.items()):
        for va, vb in variants((a, b)):
            if (va, vb) not in bigrams:
                bigrams[(va, vb)] = f - VARIANT_PENALTY
    for (a, b, c), f in list(trigrams.items()):
        for v in variants((a, b, c)):
            if v not in trigrams:
                trigrams[v] = f - VARIANT_PENALTY

    english = {"good", "morning", "night", "happy", "birthday", "wish", "you", "a",
               "very", "to", "do", "the", "needful", "kindly", "please", "revert",
               "back", "time", "wait", "office", "problem", "plan", "scene", "number",
               "phone", "Diwali", "Holi", "Eid", "Mubarak"}
    for pair in bigrams:
        vocab.update(pair)
    for triple in trigrams:
        vocab.update(triple)
    vocab -= english

    header = "# Generated by tools/make_hinglish.py - edit that file, not this one.\n"
    (DATA / "hinglish_vocab.txt").write_text(
        header + "\n".join(sorted(vocab)) + "\n", encoding="utf-8")
    (DATA / "hinglish_bigrams.txt").write_text(
        header + "".join(f"{a} {b} {f}\n" for (a, b), f in sorted(bigrams.items())),
        encoding="utf-8")
    (DATA / "hinglish_trigrams.txt").write_text(
        header + "".join(f"{a} {b} {c} {f}\n" for (a, b, c), f in sorted(trigrams.items())),
        encoding="utf-8")
    print(f"{len(vocab)} words, {len(bigrams)} bigrams, {len(trigrams)} trigrams")


if __name__ == "__main__":
    main()
