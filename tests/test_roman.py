"""Hindi captions and Arabic-script recognition mistakes come out in Roman Hinglish, never translated.
The AI is replaced by a stand-in, so nothing leaves this machine."""
import os, sys, tempfile
os.environ["PEAKCUT_DATA"] = tempfile.mkdtemp(prefix="pc-roman-"); os.environ["DATABASE_URL"] = ""
sys.path.insert(0, ".")
from studio import brain, roman
fails = []
def check(n, ok, x=""):
    print(("PASS " if ok else "FAIL ") + n + (f"  {x}" if x and not ok else "")); ok or fails.append(n)
def ws(text):
    return [{"w": w, "s": i * 0.5, "e": i * 0.5 + 0.4} for i, w in enumerate(text.split())]
def text(words):
    return " ".join(w["w"] for w in words)

# ---- the spelling rules on their own
for hi, want in [("चूना जो उसको", "chuna jo usko"), ("कहना करता समझना", "kahna karta samajhna"), ("आज", "aaj"),
                 ("ज़िंदगी", "zindagi"), ("नहीं यार", "nahi yaar"), ("बात", "baat"), ("हमारा", "hamara"),
                 ("GTA गेम में 1000", "GTA gem mein 1000")]:
    check(f"{hi} -> {want}", roman.to_roman(hi) == want, roman.to_roman(hi))
check("English is left alone", roman.to_roman("Hello there, 25 cars!") == "Hello there, 25 cars!")

# ---- with no AI: every Hindi word is spelled out, at the same moment
def no_ai(*a, **k):
    raise RuntimeError("The AI is not set up on this server.")
brain.ask_ai = no_ai
src = ws("अरे चूना जो उसको लगा")
out = brain.fix_caption_words(src, "test")
check("without AI, Hindi captions come out in Roman letters", text(out) == "are chuna jo usko laga", text(out))
check("...with every word at its own time", [(w["s"], w["e"]) for w in out] == [(w["s"], w["e"]) for w in src])
check("short clips are spelled out too", text(brain.fix_caption_words(ws("जो उसको"), "")) == "jo usko")

# ---- with the AI: its Hinglish is used, a translation is not, and other scripts/languages are handled
answers = {}
def fake_ai(prompt, schema=None, purpose=""):
    return answers["now"], "m", 10
brain.ask_ai = fake_ai
answers["now"] = ["Arre", "choona", "jo", "usko", "laga."]
check("the AI's Hinglish spelling is used", text(brain.fix_caption_words(src, "")) == "Arre choona jo usko laga.")
answers["now"] = ["Hey", "lime", "that", "him", "hit"]
out = text(brain.fix_caption_words(src, ""))
check("a translation is refused: the word is spelled out instead", out == "are chuna jo usko laga", out)
answers["now"] = ["Arre", "चूना", "jo", "usko", "laga"]
check("Hindi the AI left in its script is still spelled out", text(brain.fix_caption_words(src, "")) == "Arre chuna jo usko laga")
misread = ws("یار یہ کیا ہے")
answers["now"] = ["Yaar", "ye", "kya", "hai"]
check("Arabic-script speech recognition output becomes Roman Hinglish", text(brain.fix_caption_words(misread, "")) == "Yaar ye kya hai")
spanish = ws("hola amigo que pasa")
answers["now"] = ["Hola", "amigo,", "¿qué", "pasa?"]
check("Spanish stays Spanish", text(brain.fix_caption_words(spanish, "")) == "Hola amigo, ¿qué pasa?")
answers["now"] = ["one", "two"]
check("an answer of the wrong length keeps the words, in Roman letters", text(brain.fix_caption_words(src, "")) == "are chuna jo usko laga")

# ---- what the AI writes for the screen
c = brain._tidy({"hook": "चूना लगा", "title": "उसको चूना", "highlight_words": ["चूना", "boss"], "score": 90}, 1, 20)
check("hook, title and highlighted words are in Roman letters", (c["hook"], c["title"], c["highlight_words"]) == ("CHUNA LAGA", "usko chuna", ["chuna", "boss"]), str(c))

print("ALL PASSED" if not fails else f"{len(fails)} failed")
import shutil; shutil.rmtree(os.environ["PEAKCUT_DATA"], ignore_errors=True)
sys.exit(1 if fails else 0)
