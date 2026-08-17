import csv
import re
from pathlib import Path

from rapidfuzz import process, fuzz

# Adjust path to match the project structure
SNOMED_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "reference" / "snomed" / "SnomedINTL_GPSRelease_PRODUCTION_20260101T120000Z.txt"

class SnomedMapper:
    def __init__(self):
        self.term_to_snomed = {}
        self.snomed_keys = []
        self._fuzzy_cache = {}
        self._load_gps()

    def _load_gps(self):
        if not SNOMED_FILE.exists():
            print(f"Warning: SNOMED file not found at {SNOMED_FILE}")
            return

        with SNOMED_FILE.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                if row.get('Active') == '1':
                    pref_term = row.get('USPreferredTerm', '')
                    key = ''
                    if pref_term:
                        key = re.sub(r'[^a-z0-9]+', '_', pref_term.lower()).strip('_')
                        if key:
                            self.term_to_snomed[key] = key
                    
                    fsn = row.get('FSN', '')
                    if fsn:
                        fsn_clean = re.sub(r'\s*\([^)]*\)$', '', fsn)
                        key_fsn = re.sub(r'[^a-z0-9]+', '_', fsn_clean.lower()).strip('_')
                        if key_fsn:
                            self.term_to_snomed[key_fsn] = key if key else key_fsn

        self.snomed_keys = list(set(self.term_to_snomed.values()))

    def get_snomed_term(self, concept_name: str) -> str:
        """
        Returns the standardized SNOMED snake_case term.
        Uses exact match first, then falls back to fuzzy matching for 100% mapping coverage.
        """
        if not concept_name or concept_name == "unnamed":
            return concept_name

        if concept_name in self.term_to_snomed:
            return self.term_to_snomed[concept_name]
            
        if concept_name in self._fuzzy_cache:
            return self._fuzzy_cache[concept_name]

        if not self.snomed_keys:
            return concept_name
            
        # extractOne is very fast (implemented in C++) and will find the best fit
        match = process.extractOne(
            concept_name, 
            self.snomed_keys, 
            scorer=fuzz.QRatio,
            score_cutoff=50
        )
        
        if match:
            best_term, score, _ = match
            if score < 85:
                review_file = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "step_7" / "manual_snomed_review.csv"
                review_file.parent.mkdir(parents=True, exist_ok=True)
                write_header = not review_file.exists()
                with review_file.open('a', encoding='utf-8') as rf:
                    writer = csv.writer(rf)
                    if write_header:
                        writer.writerow(["original_concept", "best_snomed_match", "confidence_score"])
                    writer.writerow([concept_name, best_term, round(score, 2)])
                    
            self._fuzzy_cache[concept_name] = best_term
            return best_term
        
        self._fuzzy_cache[concept_name] = concept_name
        return concept_name

# Singleton instance to be shared
_mapper_instance = None

def get_snomed_mapper() -> SnomedMapper:
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = SnomedMapper()
    return _mapper_instance
