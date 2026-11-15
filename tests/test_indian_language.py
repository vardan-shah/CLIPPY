"""Hindi that Whisper misclassifies is re-decoded as Hindi for the live transcript and captions."""
import os
import shutil
import sys
import tempfile

DATA = tempfile.mkdtemp(prefix="clippy-hi-")
os.environ["PEAKCUT_DATA"] = DATA
sys.path.insert(0, ".")

from studio import roman, transcribe


class Word:
    def __init__(self, word):
        self.word, self.start, self.end = word, 0.1, 0.4


class Segment:
    def __init__(self, words):
        self.words = [Word(w) for w in words]


class Info:
    def __init__(self, language):
        self.language = language


class Recognizer:
    def __init__(self):
        self.languages = []

    def transcribe(self, _audio, language=None, **_kwargs):
        self.languages.append(language)
        if language is None:
            return iter([Segment(["یار", "کیا", "ہے"])]), Info("ur")
        return iter([Segment(["यार", "क्या", "है"])]), Info("hi")


rec = Recognizer()
got = transcribe._decode_faster([object()], rec)
text = " ".join(w["w"] for w in got[0])
roman_text = " ".join(w["w"] for w in roman.words(got[0]))
fails = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + ("" if condition else f"   {detail}"))
    if not condition:
        fails.append(name)


check("misclassified Hindi detection retries as Hindi", rec.languages == [None, "hi"], repr(rec.languages))
check("Hindi speech is re-decoded in Devanagari", text == "यार क्या है", text)
check("the live display gets Roman Hinglish without Arabic script", roman_text == "yaar kya hai", roman_text)
check("the final display contains neither Devanagari nor Arabic script",
      not roman.needs_roman(roman_text), roman_text)

print("ALL PASSED" if not fails else f"{len(fails)} failed")
shutil.rmtree(DATA, ignore_errors=True)
sys.exit(1 if fails else 0)
