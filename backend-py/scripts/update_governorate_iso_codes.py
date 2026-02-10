"""Normalize governorate_iso values to the official ISO 3166-2 codes provided.

Updates `public.ehvol_full_iso.governorate_iso` values according to a mapping
and then exits. Designed to be idempotent.
"""
import sys
from pathlib import Path
import argparse

import sqlalchemy
from sqlalchemy import text, create_engine

# Ensure backend package is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings


MAPPING = {
    'EG-MATRUH': 'EG-MT',
    'EG-ISMAILIA': 'EG-IS',
    'EG-ALEXANDRIA': 'EG-ALX',
    'EG-OTHER': 'EG-OTHER',
    'EG-SUEZ': 'EG-SUZ',
    'EG-RED-SEA': 'EG-BA',
    'EG-QALOUBYA': 'EG-KB',
    'EG-BEHAIRA': 'EG-BH',
    'EG-MENOUFYA': 'EG-MNF',
    'EG-PORT-SAID': 'EG-PTS',
    'EG-CAIRO': 'EG-C',
    'EG-KAFR-EL-SHEIKH': 'EG-KFS',
    'EG-BENI-SEWEIF': 'EG-BNS',
    'EG-DAKHALIA': 'EG-DK',
    'EG-SOUTH-SINAI': 'EG-JS',
    'EG-ASSUIT': 'EG-AST',
    'EG-GIZA': 'EG-GZ',
    'EG-DAMIETTA': 'EG-DT',
    'EG-QENA': 'EG-KN',
    'EG-SHARKIA': 'EG-SHR',
    'EG-GHARBYA': 'EG-GH',
    'EG-SOHAG': 'EG-SHG',
    'EG-ASWAN': 'EG-ASN',
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--table', default='ehvol_full_iso')
    p.add_argument('--schema', default='public')
    args = p.parse_args()

    engine = create_engine(settings.database_url)

    schema = args.schema
    table = args.table

    # Build CASE expression using literal strings (mapping is controlled)
    cases = []
    for src, dst in MAPPING.items():
        # safe because mapping keys/values are constants defined above
        cases.append(f"WHEN governorate_iso = '{src}' THEN '{dst}'")

    case_sql = "\n        ".join(cases)
    sql = f"UPDATE \"{schema}\".\"{table}\"\nSET governorate_iso = CASE\n        {case_sql}\n        ELSE governorate_iso END"

    print(f"Running update on {schema}.{table}...")
    with engine.begin() as conn:
        try:
            conn.execute(text(sql))
            print("Update complete.")
        except Exception as e:
            print("Failed to update governorate_iso:", e)
            sys.exit(2)


if __name__ == '__main__':
    main()
