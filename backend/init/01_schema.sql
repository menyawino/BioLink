-- EHVol PostgreSQL Schema for BioLink
-- Comprehensive cardiovascular research database

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- CORE PATIENT TABLE
-- =====================================================
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    dna_id VARCHAR(50) UNIQUE NOT NULL,
    date_of_birth DATE,
    age INTEGER,
    gender VARCHAR(20),
    is_pregnant BOOLEAN DEFAULT FALSE,
    nationality VARCHAR(100),
    father_city_origin VARCHAR(100),
    father_city_origin_alt VARCHAR(100),
    childhood_city VARCHAR(100),
    current_city VARCHAR(100),
    consent_obtained BOOLEAN DEFAULT FALSE,
    enrollment_date DATE,
    complete_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patients_dna_id ON patients(dna_id);
CREATE INDEX idx_patients_gender ON patients(gender);
CREATE INDEX idx_patients_age ON patients(age);
CREATE INDEX idx_patients_enrollment ON patients(enrollment_date);

-- =====================================================
-- LIFESTYLE & SMOKING DATA
-- =====================================================
CREATE TABLE lifestyle_data (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    current_smoker BOOLEAN DEFAULT FALSE,
    smoking_duration VARCHAR(100),
    cigarettes_per_day INTEGER,
    drinks_alcohol BOOLEAN DEFAULT FALSE,
    takes_medication BOOLEAN DEFAULT FALSE,
    ever_smoked BOOLEAN DEFAULT FALSE,
    smoking_years DECIMAL(5,2),
    complete_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lifestyle_patient ON lifestyle_data(patient_id);

-- =====================================================
-- EXCLUSION CRITERIA
-- =====================================================
CREATE TABLE exclusion_criteria (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    under_18 BOOLEAN DEFAULT FALSE,
    non_egyptian_parents BOOLEAN DEFAULT FALSE,
    known_cvs_disease BOOLEAN DEFAULT FALSE,
    known_collagen_disease BOOLEAN DEFAULT FALSE,
    communication_difficulties BOOLEAN DEFAULT FALSE,
    unwilling_to_participate BOOLEAN DEFAULT FALSE,
    pregnant_female BOOLEAN DEFAULT FALSE,
    contraindications_mri BOOLEAN DEFAULT FALSE,
    history_sudden_death BOOLEAN DEFAULT FALSE,
    history_familial_cardiomyopathies BOOLEAN DEFAULT FALSE,
    history_premature_cad BOOLEAN DEFAULT FALSE,
    complete_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_exclusion_patient ON exclusion_criteria(patient_id);

-- =====================================================
-- FAMILY & SOCIAL HISTORY
-- =====================================================
CREATE TABLE family_history (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    consanguinous_marriage_offspring BOOLEAN DEFAULT FALSE,
    parents_occupation VARCHAR(100),
    marital_status VARCHAR(50),
    consanguinous_marriage BOOLEAN DEFAULT FALSE,
    number_of_children INTEGER,
    siblings_count INTEGER,
    is_twin_or_triplet BOOLEAN DEFAULT FALSE,
    family_disease_info TEXT,
    non_cardiac_condition_family BOOLEAN DEFAULT FALSE,
    non_cardiac_condition_details TEXT,
    childhood_location VARCHAR(100),
    complete_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_family_history_patient ON family_history(patient_id);

-- =====================================================
-- MEDICAL HISTORY
-- =====================================================
CREATE TABLE medical_history (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    heart_attack_or_angina BOOLEAN DEFAULT FALSE,
    high_blood_pressure BOOLEAN DEFAULT FALSE,
    dyslipidemia BOOLEAN DEFAULT FALSE,
    rheumatic_fever BOOLEAN DEFAULT FALSE,
    anaemia BOOLEAN DEFAULT FALSE,
    lung_problems BOOLEAN DEFAULT FALSE,
    kidney_problems BOOLEAN DEFAULT FALSE,
    liver_problems BOOLEAN DEFAULT FALSE,
    diabetes_mellitus BOOLEAN DEFAULT FALSE,
    prior_heart_failure BOOLEAN DEFAULT FALSE,
    neurological_problems BOOLEAN DEFAULT FALSE,
    musculoskeletal_problems BOOLEAN DEFAULT FALSE,
    autoimmune_problems BOOLEAN DEFAULT FALSE,
    undergone_surgery BOOLEAN DEFAULT FALSE,
    procedure_details TEXT,
    malignancy BOOLEAN DEFAULT FALSE,
    comorbidity INTEGER DEFAULT 0,
    complete_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_medical_history_patient ON medical_history(patient_id);
CREATE INDEX idx_medical_history_diabetes ON medical_history(diabetes_mellitus);
CREATE INDEX idx_medical_history_hypertension ON medical_history(high_blood_pressure);

-- =====================================================
-- PHYSICAL EXAMINATION
-- =====================================================
CREATE TABLE physical_examinations (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    examination_date DATE,
    examination_type VARCHAR(50),
    heart_rate DECIMAL(6,2),
    regularity VARCHAR(50),
    bp_reading VARCHAR(50),
    systolic_bp DECIMAL(6,2),
    diastolic_bp DECIMAL(6,2),
    height_cm DECIMAL(6,2),
    weight_kg DECIMAL(6,2),
    bmi DECIMAL(6,2),
    bsa DECIMAL(6,2),
    jvp DECIMAL(6,2),
    abnormal_physical_structure BOOLEAN DEFAULT FALSE,
    s1 VARCHAR(50),
    s2 VARCHAR(50),
    s3 BOOLEAN DEFAULT FALSE,
    s4 BOOLEAN DEFAULT FALSE,
    complete_status VARCHAR(50),
    bp_outlier BOOLEAN DEFAULT FALSE,
    height_outlier BOOLEAN DEFAULT FALSE,
    weight_outlier BOOLEAN DEFAULT FALSE,
    bmi_outlier BOOLEAN DEFAULT FALSE,
    bsa_outlier BOOLEAN DEFAULT FALSE,
    systolic_outlier BOOLEAN DEFAULT FALSE,
    diastolic_outlier BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_physical_exam_patient ON physical_examinations(patient_id);
CREATE INDEX idx_physical_exam_date ON physical_examinations(examination_date);
CREATE INDEX idx_physical_exam_bmi ON physical_examinations(bmi);

-- =====================================================
-- LAB RESULTS
-- =====================================================
CREATE TABLE lab_results (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    hba1c DECIMAL(6,2),
    troponin_i DECIMAL(10,6),
    hba1c_outlier BOOLEAN DEFAULT FALSE,
    troponin_outlier BOOLEAN DEFAULT FALSE,
    heart_rate_outlier BOOLEAN DEFAULT FALSE,
    complete_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lab_results_patient ON lab_results(patient_id);

-- =====================================================
-- ECG DATA
-- =====================================================
CREATE TABLE ecg_data (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    rate DECIMAL(6,2),
    rate_clean DECIMAL(6,2),
    rhythm VARCHAR(50),
    p_wave_abnormality BOOLEAN DEFAULT FALSE,
    pr_interval DECIMAL(6,2),
    qrs_duration DECIMAL(6,2),
    qrs_abnormalities BOOLEAN DEFAULT FALSE,
    st_segment_abnormalities BOOLEAN DEFAULT FALSE,
    qtc_interval DECIMAL(6,2),
    t_wave_abnormalities BOOLEAN DEFAULT FALSE,
    ecg_conclusion VARCHAR(100),
    missing_ecg BOOLEAN DEFAULT FALSE,
    complete_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ecg_patient ON ecg_data(patient_id);
CREATE INDEX idx_ecg_conclusion ON ecg_data(ecg_conclusion);

-- =====================================================
-- ECHO DATA
-- =====================================================
CREATE TABLE echo_data (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    echo_date DATE,
    aortic_root DECIMAL(6,2),
    left_atrium DECIMAL(6,2),
    right_ventricle DECIMAL(6,2),
    lvedd DECIMAL(6,2),
    lvesd DECIMAL(6,2),
    ivsd DECIMAL(6,2),
    ivss DECIMAL(6,2),
    lvpwd DECIMAL(6,2),
    lvpws DECIMAL(6,2),
    ef DECIMAL(6,2),
    fs DECIMAL(6,2),
    subaortic_membrane BOOLEAN DEFAULT FALSE,
    mitral_regurge VARCHAR(50),
    mitral_stenosis BOOLEAN DEFAULT FALSE,
    tricuspid_regurge VARCHAR(50),
    tricuspid_stenosis BOOLEAN DEFAULT FALSE,
    aortic_regurge VARCHAR(50),
    aortic_stenosis BOOLEAN DEFAULT FALSE,
    pulmonary_regurge VARCHAR(50),
    pulmonary_stenosis BOOLEAN DEFAULT FALSE,
    missing_echo BOOLEAN DEFAULT FALSE,
    complete_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_echo_patient ON echo_data(patient_id);
CREATE INDEX idx_echo_date ON echo_data(echo_date);
CREATE INDEX idx_echo_ef ON echo_data(ef);

-- =====================================================
-- MRI DATA
-- =====================================================
CREATE TABLE mri_data (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    mri_performed BOOLEAN DEFAULT FALSE,
    heart_rate_during_mri DECIMAL(6,2),
    mri_date DATE,
    lv_ejection_fraction DECIMAL(6,2),
    lv_end_diastolic_volume DECIMAL(8,2),
    lv_end_systolic_volume DECIMAL(8,2),
    lv_mass DECIMAL(8,2),
    rv_ejection_fraction DECIMAL(6,2),
    missing_mri BOOLEAN DEFAULT FALSE,
    missing_ecg_echo_mri BOOLEAN DEFAULT FALSE,
    complete_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mri_patient ON mri_data(patient_id);
CREATE INDEX idx_mri_date ON mri_data(mri_date);
CREATE INDEX idx_mri_lv_ef ON mri_data(lv_ejection_fraction);

-- =====================================================
-- GEOGRAPHIC DATA
-- =====================================================
CREATE TABLE geographic_data (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
    current_city_category VARCHAR(50),
    childhood_city_category VARCHAR(50),
    migration_pattern VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_geographic_patient ON geographic_data(patient_id);
CREATE INDEX idx_geographic_current ON geographic_data(current_city_category);
CREATE INDEX idx_geographic_migration ON geographic_data(migration_pattern);

-- =====================================================
-- ANALYTICS VIEWS
-- =====================================================

-- Patient summary view
CREATE VIEW patient_summary AS
SELECT 
    p.id,
    p.dna_id,
    p.age,
    p.gender,
    p.nationality,
    p.enrollment_date,
    pe.heart_rate,
    pe.systolic_bp,
    pe.diastolic_bp,
    pe.bmi,
    lr.hba1c,
    lr.troponin_i,
    ed.ef as echo_ef,
    md.lv_ejection_fraction as mri_ef,
    mh.diabetes_mellitus,
    mh.high_blood_pressure,
    mh.comorbidity,
    gd.current_city_category,
    gd.migration_pattern
FROM patients p
LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
LEFT JOIN lab_results lr ON p.id = lr.patient_id
LEFT JOIN echo_data ed ON p.id = ed.patient_id
LEFT JOIN mri_data md ON p.id = md.patient_id
LEFT JOIN medical_history mh ON p.id = mh.patient_id
LEFT JOIN geographic_data gd ON p.id = gd.patient_id;

-- Demographics analytics view
CREATE VIEW demographics_analytics AS
SELECT
    CASE 
        WHEN age < 30 THEN '18-29'
        WHEN age BETWEEN 30 AND 39 THEN '30-39'
        WHEN age BETWEEN 40 AND 49 THEN '40-49'
        WHEN age BETWEEN 50 AND 59 THEN '50-59'
        WHEN age BETWEEN 60 AND 69 THEN '60-69'
        WHEN age >= 70 THEN '70+'
    END as age_group,
    gender,
    COUNT(*) as count
FROM patients
WHERE age IS NOT NULL AND gender IS NOT NULL
GROUP BY age_group, gender
ORDER BY age_group;

-- Clinical metrics view
CREATE VIEW clinical_metrics AS
SELECT
    p.id,
    p.dna_id,
    p.age,
    p.gender,
    pe.bmi,
    pe.systolic_bp,
    pe.diastolic_bp,
    lr.hba1c,
    ed.ef,
    CASE 
        WHEN pe.systolic_bp >= 140 OR pe.diastolic_bp >= 90 THEN 'High'
        WHEN pe.systolic_bp >= 120 OR pe.diastolic_bp >= 80 THEN 'Elevated'
        ELSE 'Normal'
    END as bp_status,
    CASE
        WHEN pe.bmi >= 30 THEN 'Obese'
        WHEN pe.bmi >= 25 THEN 'Overweight'
        WHEN pe.bmi >= 18.5 THEN 'Normal'
        ELSE 'Underweight'
    END as bmi_category
FROM patients p
LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
LEFT JOIN lab_results lr ON p.id = lr.patient_id
LEFT JOIN echo_data ed ON p.id = ed.patient_id;

-- Risk factors summary
CREATE VIEW risk_factors_summary AS
SELECT
    p.id,
    p.dna_id,
    mh.diabetes_mellitus,
    mh.high_blood_pressure,
    mh.dyslipidemia,
    ld.current_smoker,
    ld.ever_smoked,
    CASE WHEN pe.bmi >= 30 THEN TRUE ELSE FALSE END as obese,
    mh.heart_attack_or_angina,
    fh.history_sudden_death,
    fh.history_premature_cad,
    (
        CASE WHEN mh.diabetes_mellitus THEN 1 ELSE 0 END +
        CASE WHEN mh.high_blood_pressure THEN 1 ELSE 0 END +
        CASE WHEN mh.dyslipidemia THEN 1 ELSE 0 END +
        CASE WHEN ld.current_smoker THEN 1 ELSE 0 END +
        CASE WHEN pe.bmi >= 30 THEN 1 ELSE 0 END
    ) as risk_score
FROM patients p
LEFT JOIN medical_history mh ON p.id = mh.patient_id
LEFT JOIN lifestyle_data ld ON p.id = ld.patient_id
LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
LEFT JOIN exclusion_criteria fh ON p.id = fh.patient_id;

-- Data completeness view
CREATE VIEW data_completeness AS
SELECT
    p.id,
    p.dna_id,
    CASE WHEN pe.id IS NOT NULL THEN TRUE ELSE FALSE END as has_physical_exam,
    CASE WHEN lr.id IS NOT NULL THEN TRUE ELSE FALSE END as has_lab_results,
    CASE WHEN ecg.id IS NOT NULL THEN TRUE ELSE FALSE END as has_ecg,
    CASE WHEN ed.id IS NOT NULL AND ed.missing_echo = FALSE THEN TRUE ELSE FALSE END as has_echo,
    CASE WHEN md.id IS NOT NULL AND md.missing_mri = FALSE THEN TRUE ELSE FALSE END as has_mri,
    (
        (CASE WHEN pe.id IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN lr.id IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN ecg.id IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN ed.id IS NOT NULL AND ed.missing_echo = FALSE THEN 20 ELSE 0 END) +
        (CASE WHEN md.id IS NOT NULL AND md.missing_mri = FALSE THEN 20 ELSE 0 END)
    ) as completeness_score
FROM patients p
LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
LEFT JOIN lab_results lr ON p.id = lr.patient_id
LEFT JOIN ecg_data ecg ON p.id = ecg.patient_id
LEFT JOIN echo_data ed ON p.id = ed.patient_id
LEFT JOIN mri_data md ON p.id = md.patient_id;

-- Geographic distribution
CREATE VIEW geographic_distribution AS
SELECT
    gd.current_city_category,
    gd.migration_pattern,
    COUNT(*) as patient_count,
    AVG(p.age) as avg_age,
    COUNT(CASE WHEN p.gender = 'Male' THEN 1 END) as male_count,
    COUNT(CASE WHEN p.gender = 'Female' THEN 1 END) as female_count
FROM geographic_data gd
JOIN patients p ON gd.patient_id = p.id
GROUP BY gd.current_city_category, gd.migration_pattern;
