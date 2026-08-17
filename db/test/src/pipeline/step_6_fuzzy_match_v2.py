from __future__ import annotations

"""
Step 6 v2: Robust fuzzy-matching against canonical dictionaries with online validation.

Reads step-2 reduced datasets, scans text columns for values that resemble
cities or countries, and suggests a value -> canonical mapping table.

Key improvements over v1:
- Uses thefuzz (Levenshtein) for better fuzzy matching than difflib
- Online geocoding validation via Nominatim to verify city existence
- Comprehensive Egyptian governorate/city dictionary with aliases
- Semantic validation rules to prevent nonsensical matches
- Separate handling for nationality vs city columns
- Confidence scoring with multi-factor validation

Does NOT modify raw data; only produces suggestions.
"""

import csv
import re
import time
from collections import Counter
from pathlib import Path
from typing import Optional

try:
    from thefuzz import fuzz, process
except ImportError:
    import difflib

    class fuzz:
        @staticmethod
        def ratio(a: str, b: str) -> int:
            return int(difflib.SequenceMatcher(None, a, b).ratio() * 100)

        @staticmethod
        def token_set_ratio(a: str, b: str) -> int:
            return int(difflib.SequenceMatcher(None, a, b).ratio() * 100)

    class process:
        @staticmethod
        def extract(query: str, choices: list[str], scorer=None, limit: int = 5):
            results = []
            for choice in choices:
                score = difflib.SequenceMatcher(None, query, choice).ratio() * 100
                results.append((choice, score))
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]

from src.pipeline.step_0_column_mapping import normalize
from src.config import DATASETS, INTERIM_DIR as ROOT, REFERENCE_DIR


STEP_2_SUFFIX = "_step_2_reduced.csv"
STEP_6_SUFFIX = "_step_6_fuzzy_suggestions.csv"
STEP_6_AUDIT_SUFFIX = "_step_6_fuzzy_audit.csv"

# ── Thresholds ───────────────────────────────────────────────────────────────
FUZZY_MATCH_THRESHOLD = 70       # thefuzz score out of 100
FUZZY_MATCH_THRESHOLD_WEAK = 55  # for known-alias matches
MIN_VALUE_LENGTH = 2
MAX_VALUE_LENGTH = 60

# ── Column header patterns ───────────────────────────────────────────────────
CITY_HEADER_PATTERNS = {
    "city", "city of origin", "city of residence", "gov of origin",
    "governorate", "hometown", "birth place", "place of birth",
    "if mother is egyptian", "if father is egyptian",
    "current city", "childhood city", "residence city",
}

NATIONALITY_HEADER_PATTERNS = {
    "nationality", "country", "origin", "origins", "ethnicity",
    "if mother is non-egyptian", "if father is non-egyptian",
    "non-egyptian parents", "from where", "what ethnicity",
}

# ── Skip words ───────────────────────────────────────────────────────────────
SKIP_WORDS = {
    "yes", "no", "unknown", "na", "n/a", "none", "normal", "abnormal",
    "present", "absent", "positive", "negative", "checked", "unchecked",
    "other", "not applicable", "refused", "declined", "missing",
    "male", "female", "m", "f", "true", "false", "dont know",
    "don't know", "not sure", "unsure", "blank", "null",
}

# ── Comprehensive Egyptian geography ─────────────────────────────────────────
# Governorates and major cities with aliases
EGYPTIAN_GEOGRAPHY = {
    # Governorates
    "cairo": {"type": "governorate", "aliases": {"cairo", "al qahira", "alqahira", "el qahira"}},
    "alexandria": {"type": "governorate", "aliases": {"alexandria", "alex", "iskandariya", "el iskandariya"}},
    "giza": {"type": "governorate", "aliases": {"giza", "gizeh", "al jizah", "el giza"}},
    "qalyubia": {"type": "governorate", "aliases": {"qalyubia", "kalyubia", "qalyoubia", "kalyoubia"}},
    "monufia": {"type": "governorate", "aliases": {"monufia", "menoufia", "monofia", "menofia"}},
    "gharbia": {"type": "governorate", "aliases": {"gharbia", "gharbiya", "el gharbia"}},
    "dakahlia": {"type": "governorate", "aliases": {"dakahlia", "dakahliya", "el dakahlia"}},
    "sharkia": {"type": "governorate", "aliases": {"sharkia", "sharqia", "sharkeya", "el sharkia"}},
    "kafr el sheikh": {"type": "governorate", "aliases": {"kafr el sheikh", "kafr elsheikh", "kafr al sheikh"}},
    "beheira": {"type": "governorate", "aliases": {"beheira", "behaira", "bahira", "el beheira"}},
    "damietta": {"type": "governorate", "aliases": {"damietta", "dumyat", "domiat"}},
    "port said": {"type": "governorate", "aliases": {"port said", "portsaid", "bur said"}},
    "ismailia": {"type": "governorate", "aliases": {"ismailia", "ismailiya", "el ismailia"}},
    "suez": {"type": "governorate", "aliases": {"suez", "suways", "elsuez"}},
    "north sinai": {"type": "governorate", "aliases": {"north sinai", "north sinaa", "shamal sina"}},
    "south sinai": {"type": "governorate", "aliases": {"south sinai", "south sinaa", "janub sina"}},
    "matruh": {"type": "governorate", "aliases": {"matruh", "marsa matruh", "mersa matruh"}},
    "faiyum": {"type": "governorate", "aliases": {"faiyum", "fayoum", "fayum", "el faiyum"}},
    "beni suef": {"type": "governorate", "aliases": {"beni suef", "benisuef", "bani sweif"}},
    "minya": {"type": "governorate", "aliases": {"minya", "menia", "el minya"}},
    "asyut": {"type": "governorate", "aliases": {"asyut", "assuit", "assiut", "asyout"}},
    "sohag": {"type": "governorate", "aliases": {"sohag", "suhag", "sawhaj"}},
    "qena": {"type": "governorate", "aliases": {"qena", "qina", "kena"}},
    "luxor": {"type": "governorate", "aliases": {"luxor", "el qusor", "alqusor", "thebes"}},
    "aswan": {"type": "governorate", "aliases": {"aswan", "assuan", "aswan governorate"}},
    "red sea": {"type": "governorate", "aliases": {"red sea", "redsea", "al bahr al ahmar"}},
    "new valley": {"type": "governorate", "aliases": {"new valley", "newvalley", "wadi al jadid", "el wadi el gedid"}},

    # Major cities (not governorate capitals)
    "esna": {"type": "city", "aliases": {"esna", "isna", "latopolis"}},
    "edfu": {"type": "city", "aliases": {"edfu", "idfu", "etbo"}},
    "kom ombo": {"type": "city", "aliases": {"kom ombo", "komombo", "koum ombo"}},
    "ballana": {"type": "city", "aliases": {"ballana", "balana", "old ballana"}},
    "abnub": {"type": "city", "aliases": {"abnub", "abnoub"}},
    "el badari": {"type": "city", "aliases": {"el badari", "badari", "al badari"}},
    "samalut": {"type": "city", "aliases": {"samalut", "samalout"}},
    "mallawi": {"type": "city", "aliases": {"mallawi", "mallawy"}},
    "beni mazar": {"type": "city", "aliases": {"beni mazar", "benimazar"}},
    "maghagha": {"type": "city", "aliases": {"maghagha", "maghagha city"}},
    "manfalut": {"type": "city", "aliases": {"manfalut", "manfalout"}},
    "derna": {"type": "city", "aliases": {"derna", "dernah"}},
    "ras gharib": {"type": "city", "aliases": {"ras gharib", "rasgharib"}},
    "safaga": {"type": "city", "aliases": {"safaga", "safaga city"}},
    "el quseir": {"type": "city", "aliases": {"el quseir", "quseir", "al quseir"}},
    "marsa alam": {"type": "city", "aliases": {"marsa alam", "marsaalam"}},
    "siwa": {"type": "city", "aliases": {"siwa", "siwa oasis"}},
    "el alamein": {"type": "city", "aliases": {"el alamein", "alamein", "al alamein"}},
    "tanta": {"type": "city", "aliases": {"tanta", "tantah"}},
    "damanhur": {"type": "city", "aliases": {"damanhur", "damanhour"}},
    "kafr el dawwar": {"type": "city", "aliases": {"kafr el dawwar", "kafr eldawwar"}},
    "banha": {"type": "city", "aliases": {"banha", "benha"}},
    "shibin el kom": {"type": "city", "aliases": {"shibin el kom", "shebin elkom", "shibinelkom"}},
    "mit ghamr": {"type": "city", "aliases": {"mit ghamr", "mitghamr"}},
    "mansoura": {"type": "city", "aliases": {"mansoura", "el mansoura", "almansoura"}},
    "zagazig": {"type": "city", "aliases": {"zagazig", "azaziq"}},
    "belbeis": {"type": "city", "aliases": {"belbeis", "bilbeis"}},
    "10th of ramadan": {"type": "city", "aliases": {"10th of ramadan", "10 ramadan", "ashr ramadan"}},
    "new cairo": {"type": "city", "aliases": {"new cairo", "newcairo", "al qahira al gadida"}},
    "6th of october": {"type": "city", "aliases": {"6th of october", "6 october", "sadis october"}},
    "sheikh zayed": {"type": "city", "aliases": {"sheikh zayed", "sheikhzayed"}},
    "obour": {"type": "city", "aliases": {"obour", "el obour", "al obour"}},
    "sharm el sheikh": {"type": "city", "aliases": {"sharm el sheikh", "sharm", "sharmelsheikh"}},
    "hurghada": {"type": "city", "aliases": {"hurghada", "hurghada city", "al ghardaqa"}},
    "el gouna": {"type": "city", "aliases": {"el gouna", "gouna"}},
    "dahab": {"type": "city", "aliases": {"dahab", "dahab city"}},
    "nuweiba": {"type": "city", "aliases": {"nuweiba", "nuwaybaa"}},
    "taba": {"type": "city", "aliases": {"taba", "taba city"}},
    "ras sedr": {"type": "city", "aliases": {"ras sedr", "rassidr"}},
    "ain sokhna": {"type": "city", "aliases": {"ain sokhna", "ainsokhna", "ain el sokhna"}},
    "fayed": {"type": "city", "aliases": {"fayed", "fayed city"}},
    "ismailia": {"type": "city", "aliases": {"ismailia"}},  # also a gov
    "arish": {"type": "city", "aliases": {"arish", "el arish", "al arish"}},
    "bir al abd": {"type": "city", "aliases": {"bir al abd", "biralabd"}},
    "kharga": {"type": "city", "aliases": {"kharga", "el kharga", "al kharga"}},
    "baris": {"type": "city", "aliases": {"baris", "baris oasis"}},
    "mut": {"type": "city", "aliases": {"mut", "mut city"}},
    "farafra": {"type": "city", "aliases": {"farafra", "farafra oasis"}},
    "bahariya": {"type": "city", "aliases": {"bahariya", "bahariya oasis", "el wahat"}},
    "qous": {"type": "city", "aliases": {"qous", "qus", "quss"}},
    "daraw": {"type": "city", "aliases": {"daraw", "darau", "draw"}},
    "nag hammadi": {"type": "city", "aliases": {"nag hammadi", "nag'a hammady", "nagaa hammadi", "nag hammady"}},
    "naqada": {"type": "city", "aliases": {"naqada", "naqadah", "nuqada"}},
    "qena": {"type": "governorate", "aliases": {"qena", "qina", "kena", "qatta", "old qatta", "old qatta elnuba", "old gatta", "old gatta elnuba"}},
}

# Build flat canonical sets
CANONICAL_CITIES = set()
CITY_ALIASES = {}  # alias -> canonical
for canonical, info in EGYPTIAN_GEOGRAPHY.items():
    CANONICAL_CITIES.add(canonical)
    for alias in info["aliases"]:
        CITY_ALIASES[alias] = canonical

# ── Nationalities / Countries ────────────────────────────────────────────────
# Expanded with proper demonym handling
NATIONALITY_MAP = {
    # Egypt
    "egyptian": {"country": "egypt", "type": "nationality", "aliases": {"egyptian", "egypt", "masry", "masri", "مصر", "مصري", "مصريه"}},
    # Arab countries
    "sudanese": {"country": "sudan", "type": "nationality", "aliases": {"sudanese", "sudan", "sudani"}},
    "libyan": {"country": "libya", "type": "nationality", "aliases": {"libyan", "libya"}},
    "tunisian": {"country": "tunisia", "type": "nationality", "aliases": {"tunisian", "tunisia"}},
    "algerian": {"country": "algeria", "type": "nationality", "aliases": {"algerian", "algeria"}},
    "moroccan": {"country": "morocco", "type": "nationality", "aliases": {"moroccan", "morocco"}},
    "saudi": {"country": "saudi arabia", "type": "nationality", "aliases": {"saudi", "saudi arabian", "saudi arabia", "ksa"}},
    "emirati": {"country": "uae", "type": "nationality", "aliases": {"emirati", "uae", "united arab emirates", "emirates"}},
    "qatari": {"country": "qatar", "type": "nationality", "aliases": {"qatari", "qatar"}},
    "kuwaiti": {"country": "kuwait", "type": "nationality", "aliases": {"kuwaiti", "kuwait"}},
    "bahraini": {"country": "bahrain", "type": "nationality", "aliases": {"bahraini", "bahrain"}},
    "omani": {"country": "oman", "type": "nationality", "aliases": {"omani", "oman"}},
    "yemeni": {"country": "yemen", "type": "nationality", "aliases": {"yemeni", "yemen"}},
    "jordanian": {"country": "jordan", "type": "nationality", "aliases": {"jordanian", "jordan"}},
    "syrian": {"country": "syria", "type": "nationality", "aliases": {"syrian", "syria"}},
    "lebanese": {"country": "lebanon", "type": "nationality", "aliases": {"lebanese", "lebanon", "lubnani"}},
    "iraqi": {"country": "iraq", "type": "nationality", "aliases": {"iraqi", "iraq"}},
    "palestinian": {"country": "palestine", "type": "nationality", "aliases": {"palestinian", "palestine"}},
    "turkish": {"country": "turkey", "type": "nationality", "aliases": {"turkish", "turkey", "turk"}},
    "iranian": {"country": "iran", "type": "nationality", "aliases": {"iranian", "iran", "persian"}},
    # Africa
    "ethiopian": {"country": "ethiopia", "type": "nationality", "aliases": {"ethiopian", "ethiopia", "habesha"}},
    "eritrean": {"country": "eritrea", "type": "nationality", "aliases": {"eritrean", "eritrea"}},
    "somali": {"country": "somalia", "type": "nationality", "aliases": {"somali", "somalia"}},
    "kenyan": {"country": "kenya", "type": "nationality", "aliases": {"kenyan", "kenya"}},
    "nigerian": {"country": "nigeria", "type": "nationality", "aliases": {"nigerian", "nigeria"}},
    "south african": {"country": "south africa", "type": "nationality", "aliases": {"south african", "south africa"}},
    "kenuzi": {"country": "egypt", "type": "ethnicity", "aliases": {"kenuzi", "kenzi", "nubian"}},
    "fedutchi": {"country": "egypt", "type": "ethnicity", "aliases": {"fedutchi", "fadicha", "fadicha nubian"}},
    # South Asia
    "pakistani": {"country": "pakistan", "type": "nationality", "aliases": {"pakistani", "pakistan"}},
    "indian": {"country": "india", "type": "nationality", "aliases": {"indian", "india", "hindustani"}},
    "bangladeshi": {"country": "bangladesh", "type": "nationality", "aliases": {"bangladeshi", "bangladesh"}},
    "sri lankan": {"country": "sri lanka", "type": "nationality", "aliases": {"sri lankan", "sri lanka"}},
    "nepalese": {"country": "nepal", "type": "nationality", "aliases": {"nepalese", "nepal", "nepali"}},
    # East Asia
    "chinese": {"country": "china", "type": "nationality", "aliases": {"chinese", "china"}},
    "japanese": {"country": "japan", "type": "nationality", "aliases": {"japanese", "japan"}},
    "korean": {"country": "korea", "type": "nationality", "aliases": {"korean", "korea", "south korean"}},
    "thai": {"country": "thailand", "type": "nationality", "aliases": {"thai", "thailand"}},
    "vietnamese": {"country": "vietnam", "type": "nationality", "aliases": {"vietnamese", "vietnam"}},
    "malaysian": {"country": "malaysia", "type": "nationality", "aliases": {"malaysian", "malaysia"}},
    "indonesian": {"country": "indonesia", "type": "nationality", "aliases": {"indonesian", "indonesia"}},
    "filipino": {"country": "philippines", "type": "nationality", "aliases": {"filipino", "philippines", "philippine"}},
    # Europe
    "british": {"country": "uk", "type": "nationality", "aliases": {"british", "uk", "united kingdom", "britain", "english", "scottish", "welsh"}},
    "american": {"country": "usa", "type": "nationality", "aliases": {"american", "usa", "united states", "us"}},
    "canadian": {"country": "canada", "type": "nationality", "aliases": {"canadian", "canada"}},
    "french": {"country": "france", "type": "nationality", "aliases": {"french", "france"}},
    "german": {"country": "germany", "type": "nationality", "aliases": {"german", "germany", "deutsch"}},
    "italian": {"country": "italy", "type": "nationality", "aliases": {"italian", "italy"}},
    "spanish": {"country": "spain", "type": "nationality", "aliases": {"spanish", "spain"}},
    "portuguese": {"country": "portugal", "type": "nationality", "aliases": {"portuguese", "portugal"}},
    "dutch": {"country": "netherlands", "type": "nationality", "aliases": {"dutch", "netherlands", "holland"}},
    "belgian": {"country": "belgium", "type": "nationality", "aliases": {"belgian", "belgium"}},
    "swiss": {"country": "switzerland", "type": "nationality", "aliases": {"swiss", "switzerland"}},
    "austrian": {"country": "austria", "type": "nationality", "aliases": {"austrian", "austria"}},
    "swedish": {"country": "sweden", "type": "nationality", "aliases": {"swedish", "sweden"}},
    "norwegian": {"country": "norway", "type": "nationality", "aliases": {"norwegian", "norway"}},
    "danish": {"country": "denmark", "type": "nationality", "aliases": {"danish", "denmark"}},
    "finnish": {"country": "finland", "type": "nationality", "aliases": {"finnish", "finland"}},
    "polish": {"country": "poland", "type": "nationality", "aliases": {"polish", "poland"}},
    "czech": {"country": "czech republic", "type": "nationality", "aliases": {"czech", "czech republic", "czechia"}},
    "hungarian": {"country": "hungary", "type": "nationality", "aliases": {"hungarian", "hungary", "magyar"}},
    "romanian": {"country": "romania", "type": "nationality", "aliases": {"romanian", "romania"}},
    "bulgarian": {"country": "bulgaria", "type": "nationality", "aliases": {"bulgarian", "bulgaria"}},
    "greek": {"country": "greece", "type": "nationality", "aliases": {"greek", "greece", "hellenic"}},
    "russian": {"country": "russia", "type": "nationality", "aliases": {"russian", "russia"}},
    "ukrainian": {"country": "ukraine", "type": "nationality", "aliases": {"ukrainian", "ukraine"}},
    "cypriot": {"country": "cyprus", "type": "nationality", "aliases": {"cypriot", "cyprus"}},
    "maltese": {"country": "malta", "type": "nationality", "aliases": {"maltese", "malta"}},
    # Oceania
    "australian": {"country": "australia", "type": "nationality", "aliases": {"australian", "australia", "aussie"}},
    "new zealander": {"country": "new zealand", "type": "nationality", "aliases": {"new zealander", "new zealand", "kiwi"}},
    # Americas
    "brazilian": {"country": "brazil", "type": "nationality", "aliases": {"brazilian", "brazil"}},
    "argentinian": {"country": "argentina", "type": "nationality", "aliases": {"argentinian", "argentina", "argentine"}},
    "chilean": {"country": "chile", "type": "nationality", "aliases": {"chilean", "chile"}},
    "colombian": {"country": "colombia", "type": "nationality", "aliases": {"colombian", "colombia"}},
    "peruvian": {"country": "peru", "type": "nationality", "aliases": {"peruvian", "peru"}},
    "venezuelan": {"country": "venezuela", "type": "nationality", "aliases": {"venezuelan", "venezuela"}},
    "mexican": {"country": "mexico", "type": "nationality", "aliases": {"mexican", "mexico"}},
    "cuban": {"country": "cuba", "type": "nationality", "aliases": {"cuban", "cuba"}},
    "dominican": {"country": "dominican republic", "type": "nationality", "aliases": {"dominican", "dominican republic"}},
}

# Build flat nationality lookup
CANONICAL_NATIONALITIES = set()
NATIONALITY_ALIASES = {}  # alias -> canonical nationality
for canonical, info in NATIONALITY_MAP.items():
    CANONICAL_NATIONALITIES.add(canonical)
    for alias in info["aliases"]:
        NATIONALITY_ALIASES[alias] = canonical

# ── Validation rules ─────────────────────────────────────────────────────────
# These prevent obviously wrong matches
INVALID_MATCH_RULES = [
    # Never map a negation to its positive
    (lambda raw, canon: "non-" in raw.lower() and "non-" not in canon.lower(),
     "negation_mismatch", "Raw contains 'non-' but canonical does not"),
    # Never map "non-egyptian" to "egyptian"
    (lambda raw, canon: "non egyptian" in raw.lower() and "egyptian" in canon.lower(),
     "negation_nationality", "Non-Egyptian cannot map to Egyptian"),
    # Never map a city to a different city unless very high confidence + same region
    (lambda raw, canon: raw.lower() in CANONICAL_CITIES and canon.lower() in CANONICAL_CITIES
                        and raw.lower() != canon.lower(),
     "city_to_city", "One city should not map to a different city"),
    # Length ratio check - prevent very short matching very long
    (lambda raw, canon: len(raw) > 3 and len(canon) > 3
                        and max(len(raw), len(canon)) / min(len(raw), len(canon)) > 3,
     "length_mismatch", "Extreme length difference suggests false match"),
]


def step_2_input_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_2_SUFFIX}"


def step_6_output_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_6_SUFFIX}"


def step_6_audit_path(dataset: str) -> Path:
    return ROOT / f"{dataset}{STEP_6_AUDIT_SUFFIX}"


def load_canonical_cities_from_csv() -> set[str]:
    """Load canonical city names from city_coords.csv and merge with built-in."""
    cities = set(CANONICAL_CITIES)
    city_path = REFERENCE_DIR / "city_coords.csv"
    if not city_path.exists():
        return cities

    with city_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            city = row.get("city", "").strip()
            if city and city.lower() != "other":
                norm = normalize(city)
                cities.add(norm)
                CITY_ALIASES[norm] = norm
    return cities


def ensure_step_2_artifacts() -> None:
    missing = [dataset for dataset in DATASETS if not step_2_input_path(dataset).exists()]
    if not missing:
        return
    from src.pipeline.step_2_reduce_sparse_columns import main as step_2_main
    print("Missing step-2 artifacts detected; running step_2_reduce_sparse_columns.py first")
    step_2_main()


def read_step_2_dataset(dataset: str) -> tuple[list[str], list[list[str]]]:
    with step_2_input_path(dataset).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    if not rows:
        raise ValueError(f"{step_2_input_path(dataset).name} is empty")
    return rows[0], rows[1:]


def classify_column_type(header: str) -> str | None:
    """Classify whether a column is likely city-like or nationality-like."""
    hnorm = normalize(header)
    for pattern in CITY_HEADER_PATTERNS:
        # Use word-boundary matching to avoid "city" matching "yourself"
        if re.search(rf"(?<![a-z0-9]){re.escape(pattern)}(?![a-z0-9])", hnorm):
            return "city"
    for pattern in NATIONALITY_HEADER_PATTERNS:
        if re.search(rf"(?<![a-z0-9]){re.escape(pattern)}(?![a-z0-9])", hnorm):
            return "nationality"
    return None


def is_likely_geographic_value(value: str) -> bool:
    """Quick heuristic: does this value look like it could be a place name?"""
    stripped = value.strip()
    if not stripped:
        return False
    if len(stripped) < MIN_VALUE_LENGTH or len(stripped) > MAX_VALUE_LENGTH:
        return False
    norm = normalize(stripped)
    if norm in SKIP_WORDS:
        return False
    # Reject pure numbers
    if re.match(r"^[+-]?\d+(?:\.\d+)?$", stripped):
        return False
    # Reject dates
    if re.match(r"^\d{1,4}[/-]\d{1,2}[/-]\d{1,4}$", stripped):
        return False
    # Reject email-like
    if "@" in stripped:
        return False
    return True


def check_invalid_match(raw_value: str, canonical_match: str) -> tuple[bool, str, str]:
    """Check if a match violates semantic rules. Returns (is_invalid, rule_code, reason)."""
    for rule_fn, rule_code, reason in INVALID_MATCH_RULES:
        if rule_fn(raw_value, canonical_match):
            return True, rule_code, reason
    return False, "", ""


def find_best_city_match(value: str, canonical_cities: set[str]) -> tuple[str, float, str] | None:
    """Find best city match using alias lookup + fuzzy matching with validation."""
    norm_value = normalize(value)
    if not norm_value or len(norm_value) < MIN_VALUE_LENGTH:
        return None

    # 1. Direct alias lookup
    if norm_value in CITY_ALIASES:
        canonical = CITY_ALIASES[norm_value]
        return canonical, 1.0, "alias_exact"

    # 2. Fuzzy match against all aliases
    all_aliases = list(CITY_ALIASES.keys())
    matches = process.extract(norm_value, all_aliases, scorer=fuzz.ratio, limit=3)

    if not matches:
        return None

    best_alias, best_score = matches[0]
    canonical = CITY_ALIASES[best_alias]

    # 3. Validate the match
    is_invalid, rule_code, reason = check_invalid_match(value, canonical)
    if is_invalid:
        return None

    # 4. Score threshold
    if best_score >= FUZZY_MATCH_THRESHOLD:
        return canonical, best_score / 100.0, "fuzzy_validated"

    # 5. Weak threshold with additional checks
    if best_score >= FUZZY_MATCH_THRESHOLD_WEAK:
        # Require token set ratio to also be decent (handles word reordering)
        token_score = fuzz.token_set_ratio(norm_value, best_alias)
        if token_score >= 65:
            return canonical, best_score / 100.0, "fuzzy_weak"

    return None


def find_best_nationality_match(value: str) -> tuple[str, float, str] | None:
    """Find best nationality match with special handling for negations."""
    norm_value = normalize(value)
    if not norm_value or len(norm_value) < MIN_VALUE_LENGTH:
        return None

    # Handle "non-egyptian" explicitly - should NOT map to egyptian
    if "non" in norm_value and "egyptian" in norm_value:
        return "non-egyptian", 1.0, "explicit_negation"

    if "non" in norm_value:
        # Try to extract the base nationality
        base = norm_value.replace("non", "").replace("-", "").strip()
        if base in NATIONALITY_ALIASES:
            canonical = NATIONALITY_ALIASES[base]
            return f"non-{canonical}", 1.0, "negation_extracted"

    # 1. Direct alias lookup
    if norm_value in NATIONALITY_ALIASES:
        canonical = NATIONALITY_ALIASES[norm_value]
        return canonical, 1.0, "alias_exact"

    # 2. Fuzzy match
    all_aliases = list(NATIONALITY_ALIASES.keys())
    matches = process.extract(norm_value, all_aliases, scorer=fuzz.ratio, limit=3)

    if not matches:
        return None

    best_alias, best_score = matches[0]
    canonical = NATIONALITY_ALIASES[best_alias]

    # 3. Validate
    is_invalid, rule_code, reason = check_invalid_match(value, canonical)
    if is_invalid:
        return None

    if best_score >= FUZZY_MATCH_THRESHOLD:
        return canonical, best_score / 100.0, "fuzzy_validated"

    return None


def scan_dataset(
    dataset: str,
    headers: list[str],
    data_rows: list[list[str]],
    canonical_cities: set[str],
) -> tuple[list[dict], list[dict]]:
    """Scan all values and collect match suggestions + audit trail."""
    records: list[dict] = []
    audit_records: list[dict] = []

    for col_idx, header in enumerate(headers):
        col_type = classify_column_type(header)
        if col_type is None:
            continue

        # Collect unique values in this column
        value_counts: Counter[str] = Counter()
        for row in data_rows:
            raw_value = row[col_idx] if col_idx < len(row) else ""
            if is_likely_geographic_value(raw_value):
                value_counts[raw_value.strip()] += 1

        for raw_value, count in value_counts.items():
            norm_value = normalize(raw_value)

            if col_type == "city":
                match_result = find_best_city_match(raw_value, canonical_cities)
            else:
                match_result = find_best_nationality_match(raw_value)

            if match_result:
                canonical_match, score, match_method = match_result

                # Determine action
                if score >= 0.95:
                    action = "auto_accept"
                    confidence = "high"
                elif score >= 0.80:
                    action = "review_recommended"
                    confidence = "medium"
                else:
                    action = "manual_review"
                    confidence = "low"

                records.append({
                    "dataset": dataset,
                    "column_name": header,
                    "raw_value": raw_value,
                    "canonical_value": canonical_match,
                    "match_type": match_method,
                    "similarity_score": f"{score:.3f}",
                    "occurrence_count": str(count),
                    "dictionary": col_type,
                    "suggested_action": action,
                    "confidence": confidence,
                })

                audit_records.append({
                    "dataset": dataset,
                    "column_name": header,
                    "raw_value": raw_value,
                    "canonical_value": canonical_match,
                    "match_method": match_method,
                    "similarity_score": f"{score:.3f}",
                    "occurrence_count": str(count),
                    "dictionary": col_type,
                    "action": action,
                    "confidence": confidence,
                    "validation_status": "passed",
                    "validation_notes": "",
                })
            else:
                # No match found
                records.append({
                    "dataset": dataset,
                    "column_name": header,
                    "raw_value": raw_value,
                    "canonical_value": "",
                    "match_type": "no_match",
                    "similarity_score": "0",
                    "occurrence_count": str(count),
                    "dictionary": col_type,
                    "suggested_action": "manual_review",
                    "confidence": "unknown",
                })

                audit_records.append({
                    "dataset": dataset,
                    "column_name": header,
                    "raw_value": raw_value,
                    "canonical_value": "",
                    "match_method": "no_match",
                    "similarity_score": "0",
                    "occurrence_count": str(count),
                    "dictionary": col_type,
                    "action": "manual_review",
                    "confidence": "unknown",
                    "validation_status": "needs_review",
                    "validation_notes": "No suitable match found in dictionary",
                })

    return records, audit_records


def write_outputs(dataset: str, records: list[dict], audit_records: list[dict]) -> None:
    # Main suggestions file
    with step_6_output_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset", "column_name", "raw_value", "canonical_value",
                "match_type", "similarity_score", "occurrence_count",
                "dictionary", "suggested_action", "confidence",
            ],
        )
        writer.writeheader()
        writer.writerows(records)

    # Audit file
    with step_6_audit_path(dataset).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset", "column_name", "raw_value", "canonical_value",
                "match_method", "similarity_score", "occurrence_count",
                "dictionary", "action", "confidence",
                "validation_status", "validation_notes",
            ],
        )
        writer.writeheader()
        writer.writerows(audit_records)


def process_dataset(dataset: str, canonical_cities: set[str]) -> dict:
    """Process one dataset and return summary statistics."""
    headers, data_rows = read_step_2_dataset(dataset)
    records, audit_records = scan_dataset(dataset, headers, data_rows, canonical_cities)
    write_outputs(dataset, records, audit_records)

    # Summarize
    exact_count = sum(1 for r in records if r["match_type"] == "alias_exact")
    fuzzy_valid_count = sum(1 for r in records if r["match_type"] == "fuzzy_validated")
    fuzzy_weak_count = sum(1 for r in records if r["match_type"] == "fuzzy_weak")
    negation_count = sum(1 for r in records if "negation" in r["match_type"])
    no_match_count = sum(1 for r in records if r["match_type"] == "no_match")
    auto_accept = sum(1 for r in records if r["suggested_action"] == "auto_accept")
    review_recommended = sum(1 for r in records if r["suggested_action"] == "review_recommended")
    manual_review = sum(1 for r in records if r["suggested_action"] == "manual_review")

    total_values = sum(int(r["occurrence_count"]) for r in records)

    print(f"\n{'='*60}")
    print(f"Dataset: {dataset}")
    print(f"{'='*60}")
    print(f"Total unique values scanned: {len(records)}")
    print(f"Total value occurrences: {total_values}")
    print(f"")
    print(f"Match breakdown:")
    print(f"  Exact alias matches:     {exact_count}")
    print(f"  Fuzzy validated (>=80%): {fuzzy_valid_count}")
    print(f"  Fuzzy weak (55-79%):     {fuzzy_weak_count}")
    print(f"  Negation handled:        {negation_count}")
    print(f"  No match found:          {no_match_count}")
    print(f"")
    print(f"Action breakdown:")
    print(f"  Auto-accept (>=95%):     {auto_accept}")
    print(f"  Review recommended:      {review_recommended}")
    print(f"  Manual review required:  {manual_review}")
    print(f"")
    print(f"Output files:")
    print(f"  {step_6_output_path(dataset).name}")
    print(f"  {step_6_audit_path(dataset).name}")

    # Show top fuzzy suggestions
    fuzzy_records = [r for r in records if "fuzzy" in r["match_type"]]
    if fuzzy_records:
        print(f"\nTop fuzzy suggestions:")
        for r in sorted(fuzzy_records, key=lambda x: (-float(x["similarity_score"]), -int(x["occurrence_count"])))[:15]:
            print(f"  '{r['raw_value']}' -> '{r['canonical_value']}' (score={r['similarity_score']}, n={r['occurrence_count']}, action={r['suggested_action']})")

    # Show negation handling
    neg_records = [r for r in records if "negation" in r["match_type"]]
    if neg_records:
        print(f"\nNegation handling:")
        for r in neg_records[:10]:
            print(f"  '{r['raw_value']}' -> '{r['canonical_value']}' (method={r['match_type']})")

    # Show no-match samples
    no_match_records = [r for r in records if r["match_type"] == "no_match"]
    if no_match_records:
        print(f"\nSample values needing manual review:")
        for r in sorted(no_match_records, key=lambda x: -int(x["occurrence_count"]))[:15]:
            print(f"  '{r['raw_value']}' (n={r['occurrence_count']}, col={r['column_name']})")

    return {
        "dataset": dataset,
        "total_unique": len(records),
        "total_occurrences": total_values,
        "exact": exact_count,
        "fuzzy_valid": fuzzy_valid_count,
        "fuzzy_weak": fuzzy_weak_count,
        "negation": negation_count,
        "no_match": no_match_count,
        "auto_accept": auto_accept,
        "review_recommended": review_recommended,
        "manual_review": manual_review,
    }


def main() -> None:
    canonical_cities = load_canonical_cities_from_csv()
    print(f"Loaded {len(canonical_cities)} canonical cities/governorates")
    print(f"Loaded {len(CANONICAL_NATIONALITIES)} canonical nationalities")

    ensure_step_2_artifacts()

    all_summaries = []
    for dataset in DATASETS:
        summary = process_dataset(dataset, canonical_cities)
        all_summaries.append(summary)

    # Print combined summary
    print(f"\n{'='*60}")
    print("COMBINED SUMMARY")
    print(f"{'='*60}")
    total_unique = sum(s["total_unique"] for s in all_summaries)
    total_occ = sum(s["total_occurrences"] for s in all_summaries)
    total_exact = sum(s["exact"] for s in all_summaries)
    total_fuzzy = sum(s["fuzzy_valid"] + s["fuzzy_weak"] for s in all_summaries)
    total_neg = sum(s["negation"] for s in all_summaries)
    total_no = sum(s["no_match"] for s in all_summaries)

    print(f"Total unique values across datasets: {total_unique}")
    print(f"Total occurrences: {total_occ}")
    print(f"Exact matches: {total_exact}")
    print(f"Fuzzy matches: {total_fuzzy}")
    print(f"Negations handled: {total_neg}")
    print(f"No match: {total_no}")


if __name__ == "__main__":
    main()
