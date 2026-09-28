"""Starting vocabulary: 50 everyday ISL words + fingerspelling A-Z and 1-9."""

# gloss -> INCLUDE folder (category/word). "text" is how the gloss reads in a sentence.
_WORDS = [
    # greetings
    ("HELLO", "greetings/hello", "hello"),
    ("HOW_ARE_YOU", "greetings/howareyou", "how are you"),
    ("THANK_YOU", "greetings/thankyou", "thank you"),
    ("GOOD_MORNING", "greetings/goodmorning", "good morning"),
    ("GOOD_NIGHT", "greetings/goodnight", "good night"),
    ("ALRIGHT", "greetings/alright", "alright"),
    ("PLEASED", "greetings/pleased", "pleased"),
    # pronouns
    ("I", "pronouns/i", "I"),
    ("YOU", "pronouns/you", "you"),
    ("HE", "pronouns/he", "he"),
    ("SHE", "pronouns/she", "she"),
    ("WE", "pronouns/we", "we"),
    ("THEY", "pronouns/they", "they"),
    # people
    ("MOTHER", "people/mother", "mother"),
    ("FATHER", "people/father", "father"),
    ("BROTHER", "people/brother", "brother"),
    ("SISTER", "people/sister", "sister"),
    ("FRIEND", "people/friend", "friend"),
    ("FAMILY", "people/family", "family"),
    ("BABY", "people/baby", "baby"),
    ("DOCTOR", "jobs/doctor", "doctor"),
    ("TEACHER", "jobs/teacher", "teacher"),
    ("POLICE", "jobs/police", "police"),
    # places
    ("HOSPITAL", "places/hospital", "hospital"),
    ("HOUSE", "places/house", "house"),
    ("SCHOOL", "places/school", "school"),
    ("MARKET", "places/market", "market"),
    ("BANK", "places/bank", "bank"),
    ("OFFICE", "places/office", "office"),
    ("RESTAURANT", "places/restaurant", "restaurant"),
    # describing words
    ("GOOD", "adjectives/good", "good"),
    ("BAD", "adjectives/bad", "bad"),
    ("HAPPY", "adjectives/happy", "happy"),
    ("SAD", "adjectives/sad", "sad"),
    ("SICK", "adjectives/sick", "sick"),
    ("HOT", "adjectives/hot", "hot"),
    ("COLD", "adjectives/cold", "cold"),
    ("NEW", "adjectives/new", "new"),
    ("FAST", "adjectives/fast", "fast"),
    ("SLOW", "adjectives/slow", "slow"),
    # time
    ("TODAY", "days_and_time/today", "today"),
    ("TOMORROW", "days_and_time/tomorrow", "tomorrow"),
    ("YESTERDAY", "days_and_time/yesterday", "yesterday"),
    ("MORNING", "days_and_time/morning", "morning"),
    ("NIGHT", "days_and_time/night", "night"),
    ("TIME", "days_and_time/time", "time"),
    # things
    ("MEDICINE", "society/medicine", "medicine"),
    ("MONEY", "society/money", "money"),
    ("BOOK", "home/book", "book"),
    ("BATHROOM", "home/bathroom", "bathroom"),
]

WORDS = [{"gloss": g, "source": s, "text": t} for g, s, t in _WORDS]
WORD_GLOSSES = [w["gloss"] for w in WORDS]
WORD_TEXT = {w["gloss"]: w["text"] for w in WORDS}

LETTERS = [chr(c) for c in range(ord("A"), ord("Z") + 1)] + [str(d) for d in range(1, 10)]

# Folder names in the "ISL words with landmarks" video dataset that match our glosses.
WORD_VIDEO_FOLDERS = {w["source"].split("/")[1]: w["gloss"] for w in WORDS}
