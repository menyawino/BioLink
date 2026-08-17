#!/usr/bin/env python3
"""
Manual curation of BERT column matches.
Reads bert_column_matches.csv and produces bert_column_matches_curated.csv
with a 'verdict' column: VALID, FALSE_POSITIVE, or ALREADY_MATCHED.
"""

import csv
from pathlib import Path

# Manual curation based on clinical/domain knowledge
# Format: (bhs_column, ehvol_column) -> verdict
CURATED_VERDICTS = {
    # === EXACT MATCHES (already found by exact normalization) ===
    ("Record ID", "Record ID"): "ALREADY_MATCHED",
    ("Address", "Address"): "ALREADY_MATCHED",
    ("Complete?", "Complete?"): "ALREADY_MATCHED",
    ("Date of birth", "Date of Birth"): "ALREADY_MATCHED",
    ("Gender", "Gender"): "ALREADY_MATCHED",
    ("QRS duration", "QRS duration"): "ALREADY_MATCHED",
    ("LVEDD", "LVEDD"): "ALREADY_MATCHED",
    ("LVESD", "LVESD"): "ALREADY_MATCHED",
    ("HbA1c", "HbA1c"): "ALREADY_MATCHED",
    ("BMI", "BMI"): "ALREADY_MATCHED",
    ("Heart rate", "Heart Rate"): "ALREADY_MATCHED",
    ("Consent obtained", " Consent obtained? "): "ALREADY_MATCHED",
    ("Weight in kg", "Weight (kg)"): "ALREADY_MATCHED",
    ("Height in cm", "Height (cm)"): "ALREADY_MATCHED",
    ("Troponin", "Troponin I"): "ALREADY_MATCHED",
    ("What is your marital status?", "Marital Status"): "ALREADY_MATCHED",
    ("Have you been diagnosed with Rheumatic Fever?", "Rheumatic Fever"): "ALREADY_MATCHED",

    # === VALID NEW MATCHES ===
    # Lifestyle
    ("Do you consume alcohol?", "Do you drink alcohol?"): "VALID",
    ("Smoking years", "How many years have you been smoking?"): "VALID",
    ("Average no. of cigarettes per day", "How many cigarettes have you been smoking a day?"): "VALID",
    ("Do you smoke shisha or cigarettes or both?", "How many cigarettes have you been smoking a day before you quit?"): "VALID",
    ("Do you smoke shisha or cigarettes or both?", "How many cigarettes have you been smoking a day?"): "VALID",
    ("Smoking years", "How long have you been smoking?"): "VALID",
    ("Average no. of cigarettes per day", "How many cigarettes have you been smoking a day before you quit?"): "VALID",
    ("Smoking Index (Current)", "Current/Recent Smoker (< 1 year)"): "VALID",

    # ECG
    ("QT interval", "QTc interval"): "VALID",
    ("corrected QT interval", "QTc interval"): "VALID",
    ("Abnormality (choice=ST-seg depression)", "Specifiy ST seg. abnormality"): "VALID",
    ("Rhythm in ECG", "Rhythm"): "VALID",
    ("Abnormality (choice=ST-seg elevation)", "Specifiy ST seg. abnormality"): "VALID",
    ("Abnormality (choice=ST-seg elevation)", "ST segment abnormalities"): "VALID",
    ("Abnormality (choice=T-wave inversion)", "Specifiy T wave abnormality"): "VALID",
    ("Abnormality (choice=T-wave inversion)", "T wave abnormalities"): "VALID",
    ("QRS width >= 120 ms", "QRS duration"): "VALID",
    ("Ventricular Rate", "Rate"): "VALID",

    # Diagnoses
    ("Acute Rheumatic Fever (choice=(55) Rheumatic fever without heart involvement)", "Rheumatic Fever"): "VALID",
    ("Acute Rheumatic Fever (choice=(56) Rheumatic fever with heart involvement)", "Rheumatic Fever"): "VALID",
    ("Acute Rheumatic Fever (choice=(57) Rheumatic chorea)", "Rheumatic Fever"): "VALID",
    ("Ischaemic heart diseases (choice=----- Unstable Angina)", "Heart Attack or Angina"): "VALID",
    ("Heart Failure (choice=(14) Acute Heart Failure)", "Prior Heart Failure (previous Hx)"): "VALID",
    ("Ischaemic heart diseases (choice=(9) Acute coronary syndrome)", "Heart Attack or Angina"): "VALID",

    # Echo
    ("Left atrial size", "Left Atrium"): "VALID",
    ("EF class", "EF"): "VALID",
    ("Date of cardiac MRI", "MRI Date"): "VALID",
    ("Cardiac MRI", "MRI"): "VALID",
    ("Aortic annulus (mid systole)", "Aortic Root"): "VALID",
    ("LV size", "LVEDD"): "VALID",
    ("PWT", "LVPWs"): "VALID",
    ("Myxomatous valve(s) (choice=Tricuspid)", "Tricuspid Stenosis"): "VALID",
    ("Myxomatous valve(s) (choice=Tricuspid)", "Tricuspid Regurge"): "VALID",
    ("Myxomatous valve(s) (choice=Mitral)", "Mitral Stenosis"): "VALID",
    ("Myxomatous valve(s) (choice=Mitral)", "Mitral Regurge"): "VALID",
    ("Myxomatous valve disease", "Mitral Stenosis"): "VALID",
    ("Myxomatous valve disease", "Mitral Regurge"): "VALID",

    # Family History
    ("Father's gov of origin", "Father's City of Origin"): "VALID",
    ("Father origins", "Father's City of Origin"): "VALID",
    ("Has anyone in your family (parents, grandparents or siblings) experienced sudden death, MI, stroke, or hospitalization due to heart failure?", "Do any of your own children, parents or siblings have any of the following health conditions (choice=Sudden unexpected death)"): "VALID",

    # Procedures
    ("Have you undergone a prior CABG? ", "Have you undergone an operation or any surgical procedures?"): "VALID",
    ("Have you had any other cardiac procedures?", "Have you undergone an operation or any surgical procedures?"): "VALID",
    ("Further plan details", "Procedure details"): "VALID",

    # Administration
    ("Upload consent scan 2", " Consent Scan "): "VALID",
    ("Upload consent scan 1", " Consent Scan "): "VALID",
    ("Agree to consent", " Consent obtained? "): "VALID",
    ("Date (Clinical Exam)", "Examination Date"): "VALID",
    ("Date (Echocardiography)", "Echo Date"): "VALID",

    # Demographics
    ("Current age", "Age"): "VALID",
    ("Participant's Name", "Name"): "VALID",

    # === FALSE POSITIVES ===
    # Echo measurement confusion
    ("LVESD", "LVM"): "FALSE_POSITIVE",
    ("LVESD", "LVPWs"): "FALSE_POSITIVE",
    ("LVESD", "LVPWd"): "FALSE_POSITIVE",
    ("LVEDD", "LVESD"): "FALSE_POSITIVE",
    ("LVESD", "LVEDD"): "FALSE_POSITIVE",
    ("LVEDD", "LVM"): "FALSE_POSITIVE",
    ("LVEDD", "LVPWd"): "FALSE_POSITIVE",

    # Family history parent mismatch
    ("Mother's gov of origin", "Father's City of Origin"): "FALSE_POSITIVE",

    # Condition vs measurement
    ("LV diastolic dysfunction", "LVEDD"): "FALSE_POSITIVE",

    # Date vs boolean/text
    ("Date (Consent)", " Consent obtained? "): "FALSE_POSITIVE",
    ("ECG - PDF", "ECG_Conclusion"): "FALSE_POSITIVE",
    ("ECG Date", "ECG_Conclusion"): "FALSE_POSITIVE",
    ("ECG - XML", "ECG_Conclusion"): "FALSE_POSITIVE",
    ("Date (Medications)", "List these medications"): "FALSE_POSITIVE",

    # Different units/concepts
    ("Smoking years", "How many cigarettes have you been smoking a day?"): "FALSE_POSITIVE",
    ("Smoking years", "Current/Recent Smoker (< 1 year)"): "FALSE_POSITIVE",
    ("Smoking years", "How many cigarettes have you been smoking a day before you quit?"): "FALSE_POSITIVE",

    # Different ECG measurements
    ("QT interval", "QRS duration"): "FALSE_POSITIVE",
    ("QT interval", "PR interval"): "FALSE_POSITIVE",
    ("QRS duration", "QTc interval"): "FALSE_POSITIVE",

    # Wave type mismatch
    ("Abnormality (choice=Pathological Q waves)", "Specifiy P wave abnormality"): "FALSE_POSITIVE",

    # Opposite concepts
    ("Agree to consent", "Unwilling to participate"): "FALSE_POSITIVE",

    # Completely different measurements
    ("PS", "FS"): "FALSE_POSITIVE",
    ("AS", "Other"): "FALSE_POSITIVE",
    ("Hip circumference in cm", "Height (cm)"): "FALSE_POSITIVE",

    # Different conditions
    ("Do any of your children have congenital malformations or diseases?", "Do any of your own children, parents or siblings have any of the following health conditions (choice=Heart Disease)"): "FALSE_POSITIVE",

    # Valve mismatch
    ("Myxomatous valve(s) (choice=Tricuspid)", "Mitral Regurge"): "FALSE_POSITIVE",
}


def main():
    input_path = Path("bert_column_matches.csv")
    output_path = Path("bert_column_matches_curated.csv")

    rows = []
    with open(input_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            bhs = row["bhs_column"]
            ehvol = row["ehvol_column"]
            key = (bhs, ehvol)
            verdict = CURATED_VERDICTS.get(key, "NEEDS_REVIEW")
            row["verdict"] = verdict
            rows.append(row)

    # Write curated output
    fieldnames = list(rows[0].keys())
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    from collections import Counter
    counts = Counter(r["verdict"] for r in rows)
    total = len(rows)

    print("=" * 70)
    print("BERT COLUMN MATCHING — MANUAL CURATION SUMMARY")
    print("=" * 70)
    print(f"Total matches reviewed: {total}")
    print(f"")
    print(f"  VALID (clinically sound):           {counts.get('VALID', 0)}")
    print(f"  ALREADY_MATCHED (by exact norm):    {counts.get('ALREADY_MATCHED', 0)}")
    print(f"  FALSE_POSITIVE (clinically wrong):  {counts.get('FALSE_POSITIVE', 0)}")
    print(f"  NEEDS_REVIEW (not yet assessed):    {counts.get('NEEDS_REVIEW', 0)}")
    print(f"")

    valid_new = [r for r in rows if r["verdict"] == "VALID"]
    print(f"Valid NEW matches to integrate: {len(valid_new)}")
    print("-" * 70)
    for r in valid_new:
        print(f"  [{r['category']}] sim={r['similarity']}")
        print(f"    BHS:   '{r['bhs_column']}'")
        print(f"    EHVol: '{r['ehvol_column']}'")
        print()

    fp = [r for r in rows if r["verdict"] == "FALSE_POSITIVE"]
    print(f"\nFalse positives filtered out: {len(fp)}")
    print("-" * 70)
    for r in fp:
        print(f"  [{r['category']}] sim={r['similarity']}")
        print(f"    BHS:   '{r['bhs_column']}'")
        print(f"    EHVol: '{r['ehvol_column']}'")
        print()

    print(f"\nCurated output saved to: {output_path}")


if __name__ == "__main__":
    main()
