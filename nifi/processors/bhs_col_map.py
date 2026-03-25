# Auto-generated — BHS column map for NiFi BiolinkSchemaStandardizerProcessor
# Source: pipeline/generate_schema_sql.py  →  standardized_columns.csv
# Format: {original_col_name: (pg_col_name, coerce_func_name)}
# DO NOT EDIT by hand; re-run pipeline/generate_schema_sql.py instead.
COLUMN_MAP = {
    'ALT': ('alt', 'to_float'),  # SDTM LB.ALT | LOINC:1742-6 | [U/L]
    'AR': ('ar', 'to_str'),  # SDTM FA.AR
    'AS': ('as', 'to_str'),  # SDTM FA.AORTSTEN
    'AST': ('ast', 'to_float'),  # SDTM LB.AST | LOINC:1920-8 | [U/L]
    'Abnormality (choice=None)': ('abnormality_choice_none', 'to_bool'),  # SDTM EG.EGABN
    'Abnormality (choice=Pathological Q waves)': ('abnormality_choice_pathological_q_waves', 'to_bool'),  # SDTM EG.EGABN
    'Abnormality (choice=ST-seg depression)': ('abnormality_choice_st_seg_depression', 'to_bool'),  # SDTM EG.EGABN
    'Abnormality (choice=ST-seg elevation)': ('abnormality_choice_st_seg_elevation', 'to_bool'),  # SDTM EG.EGABN
    'Abnormality (choice=T-wave inversion)': ('abnormality_choice_t_wave_inversion', 'to_bool'),  # SDTM EG.EGABN
    'Acute Rheumatic Fever (choice=(55) Rheumatic fever without heart involvement)': ('acute_rheumatic_fever_choice_55_rheumatic_fever_without_heart_i', 'to_bool'),  # SDTM FA.MHTERM
    'Acute Rheumatic Fever (choice=(56) Rheumatic fever with heart involvement)': ('acute_rheumatic_fever_choice_56_rheumatic_fever_with_heart_invo', 'to_bool'),  # SDTM FA.MHTERM
    'Acute Rheumatic Fever (choice=(57) Rheumatic chorea)': ('acute_rheumatic_fever_choice_57_rheumatic_chorea', 'to_bool'),  # SDTM FA.MHTERM
    'Address': ('address', 'to_str'),  # SDTM DM.SITEID
    'Age at enrollment': ('age_at_enrollment', 'to_int'),  # SDTM DM.AGE | LOINC:30525-0 | [a]
    'Age at smoking cessation': ('age_at_smoking_cessation', 'to_int'),  # SDTM SU.DUENDT
    'Age at start of smoking': ('age_at_start_of_smoking', 'to_int'),  # SDTM SU.DUSTRT
    'Agree to CMR': ('agree_to_cmr', 'to_str'),  # SDTM SV.ADMIN
    'Agree to CT': ('agree_to_ct', 'to_str'),  # SDTM SV.ADMIN
    'Agree to consent': ('agree_to_consent', 'to_str'),  # SDTM SV.ADMIN
    'Agree to have an ECG': ('agree_to_have_an_ecg', 'to_str'),  # SDTM SV.ADMIN
    'Agree to provide family history': ('agree_to_provide_family_history', 'to_str'),  # SDTM SV.ADMIN
    'Agree to undergo TTE': ('agree_to_undergo_tte', 'to_str'),  # SDTM SV.ADMIN
    'Agree to undergo carotid duplex': ('agree_to_undergo_carotid_duplex', 'to_str'),  # SDTM SV.ADMIN
    'Agree to withdraw samples for lab workup': ('agree_to_withdraw_samples_for_lab_workup', 'to_str'),  # SDTM SV.ADMIN
    'Albumin': ('albumin', 'to_float'),  # SDTM LB.ALB | LOINC:1751-7 | [g/dL]
    'Alternate contact 1 name': ('alternate_contact_1_name', 'to_str'),  # SDTM SV.ADMIN
    'Alternate contact 1 number -1': ('alternate_contact_1_number_1', 'to_str'),  # SDTM SV.ADMIN
    'Alternate contact 1 number -2': ('alternate_contact_1_number_2', 'to_str'),  # SDTM SV.ADMIN
    'Alternate contact 1 relation': ('alternate_contact_1_relation', 'to_str'),  # SDTM SV.ADMIN
    'Alternate contact 2 name': ('alternate_contact_2_name', 'to_str'),  # SDTM SV.ADMIN
    'Alternate contact 2 number -1': ('alternate_contact_2_number_1', 'to_str'),  # SDTM SV.ADMIN
    'Alternate contact 2 number -2': ('alternate_contact_2_number_2', 'to_str'),  # SDTM SV.ADMIN
    'Alternate contact 2 relation': ('alternate_contact_2_relation', 'to_str'),  # SDTM SV.ADMIN
    'Angina': ('angina', 'to_bool'),  # SDTM MH.MHTERM
    'Any modifications to the medications that  study subject has been using before recruitment to BHS?': ('any_modifications_to_the_medications_that_study_subject_has_bee', 'to_str'),  # SDTM SV.ADMIN
    'Aortic annulus (mid systole)': ('aortic_annulus_mid_systole', 'to_float'),  # SDTM FA.AOANN | LOINC:29430-6 | [mm]
    'Apex': ('apex', 'to_str'),  # SDTM FA.APEXECHO
    'Apical - Anterior': ('apical_anterior', 'to_int'),  # 
    'Apical - Inferior': ('apical_inferior', 'to_int'),  # 
    'Apical - Lateral': ('apical_lateral', 'to_int'),  # 
    'Apical - Septal': ('apical_septal', 'to_int'),  # 
    'Atheromatous plaque - left': ('atheromatous_plaque_left', 'to_bool'),  # SDTM VS.ATHPLQL
    'Atheromatous plaque - right': ('atheromatous_plaque_right', 'to_bool'),  # SDTM VS.ATHPLQR
    'Average no. of cigarettes per day': ('average_no_of_cigarettes_per_day', 'to_int'),  # SDTM SU.SUCAT
    'BMI': ('bmi', 'to_float'),  # SDTM VS.BMI | LOINC:39156-5 | [kg/m2]
    'BNP': ('bnp', 'to_float'),  # SDTM LB.BNP | LOINC:42637-9 | [pg/mL]
    'BP Pressure chart / monitoring conclusion': ('bp_pressure_chart_monitoring_conclusion', 'to_str'),  # SDTM VS.BPCONC
    'Basal - Anterior': ('basal_anterior', 'to_int'),  # 
    'Basal - Anterolateral': ('basal_anterolateral', 'to_int'),  # 
    'Basal - Anteroseptal': ('basal_anteroseptal', 'to_int'),  # 
    'Basal - Inferior': ('basal_inferior', 'to_int'),  # 
    'Basal - Inferolateral': ('basal_inferolateral', 'to_int'),  # 
    'Basal - Inferoseptal': ('basal_inferoseptal', 'to_int'),  # 
    'Brachial pressure (highest side)': ('brachial_pressure_highest_side', 'to_float'),  # SDTM VS.BRACHP | LOINC:8460-8 | [mm[Hg]]
    'CBC': ('cbc', 'to_bool'),  # SDTM SV.SVPRTRT
    'CRP': ('crp', 'to_float'),  # SDTM LB.CRP | LOINC:1988-5 | [mg/L]
    'CRP.1': ('crp_1', 'to_str'),  # 
    'CT - Specify': ('ct_specify', 'to_str'),  # SDTM SV.ADMIN
    'Ca': ('ca', 'to_float'),  # SDTM LB.CA | LOINC:17861-6 | [mg/dL]
    'Can you read and write in Arabic?': ('can_you_read_and_write_in_arabic', 'to_bool'),  # SDTM SC.SCTEST
    'Can you speak Nubian?': ('can_you_speak_nubian', 'to_bool'),  # SDTM SC.SCTEST
    'Cardiac Arrhythmias (choice=(58) Bradycardia/ bradyarrythmia)': ('cardiac_arrhythmias_choice_58_bradycardia_bradyarrythmia', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=(58.0) Sinus bradycardia)': ('cardiac_arrhythmias_choice_58_0_sinus_bradycardia', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=(58.1) Sick sinus syndrome)': ('cardiac_arrhythmias_choice_58_1_sick_sinus_syndrome', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=(58.2) Atrio-ventricular (AV) conduction block)': ('cardiac_arrhythmias_choice_58_2_atrio_ventricular_av_conduction', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=(58.2a)  ---- First degree AV block)': ('cardiac_arrhythmias_choice_58_2a_first_degree_av_block', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=(58.2b)  ---- Second degree AV block)': ('cardiac_arrhythmias_choice_58_2b_second_degree_av_block', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=(58.2c)  ---- Third degree AV block)': ('cardiac_arrhythmias_choice_58_2c_third_degree_av_block', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=(58.3) Intraventricular conduction abnormalities)': ('cardiac_arrhythmias_choice_58_3_intraventricular_conduction_abn', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=(59) Tachycardia/ tachyarrythmia)': ('cardiac_arrhythmias_choice_59_tachycardia_tachyarrythmia', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=(59.0) Supraventricular tachyarrythmia)': ('cardiac_arrhythmias_choice_59_0_supraventricular_tachyarrythmia', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=(59.1) Ventricular tachyarrythmia)': ('cardiac_arrhythmias_choice_59_1_ventricular_tachyarrythmia', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=---- Atrial fibrillation (AF))': ('cardiac_arrhythmias_choice_atrial_fibrillation_af', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=---- Atrial flutter)': ('cardiac_arrhythmias_choice_atrial_flutter', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=---- Atrial tachycardia)': ('cardiac_arrhythmias_choice_atrial_tachycardia', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=---- Premature supraventricular contractions)': ('cardiac_arrhythmias_choice_premature_supraventricular_contracti', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=---- Premature ventricular contractions)': ('cardiac_arrhythmias_choice_premature_ventricular_contractions', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=---- SVT/ PSVT/ AVRT/ AVNRT)': ('cardiac_arrhythmias_choice_svt_psvt_avrt_avnrt', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=---- Ventricular extrasystoles)': ('cardiac_arrhythmias_choice_ventricular_extrasystoles', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=---- Ventricular fibrillation (VF))': ('cardiac_arrhythmias_choice_ventricular_fibrillation_vf', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=---- Ventricular tachycardia (VT))': ('cardiac_arrhythmias_choice_ventricular_tachycardia_vt', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=---- bradycardia-tachycardia syndrome)': ('cardiac_arrhythmias_choice_bradycardia_tachycardia_syndrome', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac Arrhythmias (choice=---- sinus pauses)': ('cardiac_arrhythmias_choice_sinus_pauses', 'to_bool'),  # SDTM FA.MHTERM
    'Cardiac CT': ('cardiac_ct', 'to_bool'),  # SDTM SV.SVPRTRT
    'Cardiac MRI': ('cardiac_mri', 'to_bool'),  # SDTM SV.SVPRTRT
    'Carotid Duplex': ('carotid_duplex', 'to_bool'),  # SDTM SV.SVPRTRT
    'Category': ('category', 'to_str'),  # SDTM CM.CMCAT
    'Category.1': ('category_1', 'to_str'),  # SDTM CM.CMCAT
    'Category.10': ('category_10', 'to_str'),  # SDTM CM.CMCAT
    'Category.11': ('category_11', 'to_str'),  # SDTM CM.CMCAT
    'Category.12': ('category_12', 'to_str'),  # SDTM CM.CMCAT
    'Category.13': ('category_13', 'to_str'),  # SDTM CM.CMCAT
    'Category.14': ('category_14', 'to_str'),  # SDTM CM.CMCAT
    'Category.2': ('category_2', 'to_str'),  # SDTM CM.CMCAT
    'Category.3': ('category_3', 'to_str'),  # SDTM CM.CMCAT
    'Category.4': ('category_4', 'to_str'),  # SDTM CM.CMCAT
    'Category.5': ('category_5', 'to_str'),  # SDTM CM.CMCAT
    'Category.6': ('category_6', 'to_str'),  # SDTM CM.CMCAT
    'Category.7': ('category_7', 'to_str'),  # SDTM CM.CMCAT
    'Category.8': ('category_8', 'to_str'),  # SDTM CM.CMCAT
    'Category.9': ('category_9', 'to_str'),  # SDTM CM.CMCAT
    'Cerebrovascular diseases (choice=(53) Acute disorders of cerebral circulation)': ('cerebrovascular_diseases_choice_53_acute_disorders_of_cerebral_', 'to_bool'),  # SDTM MH.MHTERM
    'Cerebrovascular diseases (choice=(53.0) Transient ischemic attack (TIA))': ('cerebrovascular_diseases_choice_53_0_transient_ischemic_attack_', 'to_bool'),  # SDTM MH.MHTERM
    'Cerebrovascular diseases (choice=(53.1) Stroke)': ('cerebrovascular_diseases_choice_53_1_stroke', 'to_bool'),  # SDTM MH.MHTERM
    'Cerebrovascular diseases (choice=(54) Other cerebrovascular disease)': ('cerebrovascular_diseases_choice_54_other_cerebrovascular_diseas', 'to_bool'),  # SDTM MH.MHTERM
    'Cerebrovascular diseases (choice=---- Haemorrhagic stroke)': ('cerebrovascular_diseases_choice_haemorrhagic_stroke', 'to_bool'),  # SDTM MH.MHTERM
    'Cerebrovascular diseases (choice=---- Ischaemic stroke)': ('cerebrovascular_diseases_choice_ischaemic_stroke', 'to_bool'),  # SDTM FA.MHTERM
    'Clinical - Ambulatory BP monitoring': ('clinical_ambulatory_bp_monitoring', 'to_str'),  # SDTM SV.ADMIN
    'Clinical - BP chart': ('clinical_bp_chart', 'to_str'),  # SDTM SV.ADMIN
    'Clinical - Clinical follow-up': ('clinical_clinical_follow_up', 'to_str'),  # SDTM SV.ADMIN
    'Complete?': ('complete', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.1': ('complete_1', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.10': ('complete_10', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.11': ('complete_11', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.12': ('complete_12', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.13': ('complete_13', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.2': ('complete_2', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.3': ('complete_3', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.4': ('complete_4', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.5': ('complete_5', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.6': ('complete_6', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.7': ('complete_7', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.8': ('complete_8', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.9': ('complete_9', 'to_bool'),  # SDTM SV.SVCOMP
    'Complications of Heart Diseases (choice=(33) Cardiac septal defect, acquired)': ('complications_of_heart_diseases_choice_33_cardiac_septal_defect', 'to_bool'),  # SDTM FA.MHTERM
    'Complications of Heart Diseases (choice=(34) Rupture of chordae tendineae, not elsewhere classified)': ('complications_of_heart_diseases_choice_34_rupture_of_chordae_te', 'to_bool'),  # SDTM FA.MHTERM
    'Complications of Heart Diseases (choice=(35) Rupture of papillary muscle, not elsewhere classified)': ('complications_of_heart_diseases_choice_35_rupture_of_papillary_', 'to_bool'),  # SDTM FA.MHTERM
    'Complications of Heart Diseases (choice=(36) Intracardiac thrombosis, not elsewhere classified)': ('complications_of_heart_diseases_choice_36_intracardiac_thrombos', 'to_bool'),  # SDTM FA.MHTERM
    'Complications of Heart Diseases (choice=(37) Cardiomegaly)': ('complications_of_heart_diseases_choice_37_cardiomegaly', 'to_bool'),  # SDTM FA.MHTERM
    'Complications of Heart Diseases (choice=(37.0) Right ventricular hypertrophy)': ('complications_of_heart_diseases_choice_37_0_right_ventricular_h', 'to_bool'),  # SDTM FA.MHTERM
    'Complications of Heart Diseases (choice=(37.1) Left ventricular hypertrophy)': ('complications_of_heart_diseases_choice_37_1_left_ventricular_hy', 'to_bool'),  # SDTM FA.MHTERM
    'Complications of Heart Diseases (choice=(38) Postcardiotomy syndrome)': ('complications_of_heart_diseases_choice_38_postcardiotomy_syndro', 'to_bool'),  # SDTM FA.MHTERM
    'Congenital Heart Defect': ('congenital_heart_defect', 'to_str'),  # SDTM FA.CHDTERM
    'Consent obtained': ('consent_obtained', 'to_str'),  # SDTM SV.ADMIN
    'Contact number 1': ('contact_number_1', 'to_str'),  # SDTM SV.ADMIN
    'Contact number 2': ('contact_number_2', 'to_str'),  # SDTM SV.ADMIN
    'Contact number 3': ('contact_number_3', 'to_str'),  # SDTM SV.ADMIN
    'Coronary Angiography / Angioplasty / Stenting': ('coronary_angiography_angioplasty_stenting', 'to_bool'),  # SDTM PR.PRTRT
    'Coronary intervention decision (needs revision)': ('coronary_intervention_decision_needs_revision', 'to_str'),  # SDTM SV.ADMIN
    'Coronary intervention report 1': ('coronary_intervention_report_1', 'to_str'),  # SDTM SV.ADMIN
    'Coronary intervention report 2': ('coronary_intervention_report_2', 'to_str'),  # SDTM SV.ADMIN
    'Creatinine': ('creatinine', 'to_float'),  # SDTM LB.CREAT | LOINC:2160-0 | [mg/dL]
    'Current 10-Year ASCVD Risk (%)': ('current_10_year_ascvd_risk', 'to_float'),  # LOINC:79423-0 | [%]
    'Current age': ('current_age', 'to_int'),  # SDTM DM.AGE | LOINC:30525-0 | [a]
    'Date': ('date', 'to_date'),  # SDTM SV.SVSTDTC
    'Date (ABI)': ('date_abi', 'to_date'),  # SDTM SV.SVSTDTC
    'Date (Clinical Exam)': ('date_clinical_exam', 'to_date'),  # SDTM SV.SVSTDTC
    'Date (Consent)': ('date_consent', 'to_date'),  # SDTM SV.SVSTDTC
    'Date (Demographic Data)': ('date_demographic_data', 'to_date'),  # SDTM SV.SVSTDTC
    'Date (Echocardiography)': ('date_echocardiography', 'to_date'),  # SDTM FA.FADTC
    'Date (Family History)': ('date_family_history', 'to_date'),  # SDTM SV.SVSTDTC
    'Date (Medications)': ('date_medications', 'to_date'),  # SDTM SV.SVSTDTC
    'Date (Risk Factors)': ('date_risk_factors', 'to_date'),  # SDTM SV.SVSTDTC
    'Date (labs)': ('date_labs', 'to_date'),  # SDTM SV.SVSTDTC
    'Date (plan)': ('date_plan', 'to_date'),  # SDTM SV.SVSTDTC
    'Date of Cardotid Duplex': ('date_of_cardotid_duplex', 'to_date'),  # SDTM SV.SVSTDTC
    'Date of birth': ('date_of_birth', 'to_date'),  # SDTM DM.BRTHDTC | LOINC:21112-8
    'Date of cardiac CT': ('date_of_cardiac_ct', 'to_date'),  # SDTM SV.SVSTDTC
    'Date of cardiac MRI': ('date_of_cardiac_mri', 'to_date'),  # SDTM SV.SVSTDTC
    'Date of coronary intervention': ('date_of_coronary_intervention', 'to_date'),  # SDTM SV.SVSTDTC
    'Degenerative valve disease': ('degenerative_valve_disease', 'to_bool'),  # SDTM FA.DEGVALV
    'Diastolic Blood Pressure - Right Brachial - Measurement 1': ('diastolic_blood_pressure_right_brachial_measurement_1', 'to_float'),  # SDTM VS.DIABP | LOINC:8462-4 | [mm[Hg]]
    'Diastolic Blood Pressure - Right Brachial - Measurement 2': ('diastolic_blood_pressure_right_brachial_measurement_2', 'to_float'),  # SDTM VS.DIABP | LOINC:8462-4 | [mm[Hg]]
    'Diastolic Blood Pressure - Right Brachial - Measurement 3': ('diastolic_blood_pressure_right_brachial_measurement_3', 'to_float'),  # SDTM VS.DIABP | LOINC:8462-4 | [mm[Hg]]
    'Direct bilirubin': ('direct_bilirubin', 'to_float'),  # SDTM LB.DIRBILI | LOINC:1968-7 | [mg/dL]
    'Diseases of arteries, arterioles and capillaries (choice=(48) Atherosclerosis)': ('diseases_of_arteries_arterioles_and_capillaries_choice_48_ather', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=(49) Aortic aneurysm and dissection)': ('diseases_of_arteries_arterioles_and_capillaries_choice_49_aorti', 'to_bool'),  # SDTM FA.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=(49.0) Dissection of aorta (any part))': ('diseases_of_arteries_arterioles_and_capillaries_choice_49_0_dis', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=(49.1) Thoracic aortic aneurysm)': ('diseases_of_arteries_arterioles_and_capillaries_choice_49_1_tho', 'to_bool'),  # SDTM FA.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=(49.2) Abdominal aortic aneurysm)': ('diseases_of_arteries_arterioles_and_capillaries_choice_49_2_abd', 'to_bool'),  # SDTM FA.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=(49.3) Thoracoabdominal aortic aneurysm)': ('diseases_of_arteries_arterioles_and_capillaries_choice_49_3_tho', 'to_bool'),  # SDTM FA.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=(50) Other aneurysm)': ('diseases_of_arteries_arterioles_and_capillaries_choice_50_other', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=(51) Peripheral vascular disease)': ('diseases_of_arteries_arterioles_and_capillaries_choice_51_perip', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=(52) Arterial embolism and thrombosis)': ('diseases_of_arteries_arterioles_and_capillaries_choice_52_arter', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- Abdominal AA without rupture)': ('diseases_of_arteries_arterioles_and_capillaries_choice_abdomina', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- Intermittent claudication)': ('diseases_of_arteries_arterioles_and_capillaries_choice_intermit', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- Ruptured abdominal AA)': ('diseases_of_arteries_arterioles_and_capillaries_choice_ruptured', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- Ruptured thoracic AA)': ('diseases_of_arteries_arterioles_and_capillaries_choice_ruptur_2', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- Ruptured thoraco-abdominal AA)': ('diseases_of_arteries_arterioles_and_capillaries_choice_ruptur_3', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- Spasm of artery)': ('diseases_of_arteries_arterioles_and_capillaries_choice_spasm_of', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- Thoracic AA without rupture)': ('diseases_of_arteries_arterioles_and_capillaries_choice_thoracic', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- Thoraco-abdominal AA without rupture)': ('diseases_of_arteries_arterioles_and_capillaries_choice_thoraco_', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- arteriosclerosis)': ('diseases_of_arteries_arterioles_and_capillaries_choice_arterios', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- arteriosclerotic vascular disease)': ('diseases_of_arteries_arterioles_and_capillaries_choice_arteri_2', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- atheroma)': ('diseases_of_arteries_arterioles_and_capillaries_choice_atheroma', 'to_bool'),  # SDTM MH.MHTERM
    'Diseases of arteries, arterioles and capillaries (choice=---- atherosclerosis)': ('diseases_of_arteries_arterioles_and_capillaries_choice_atherosc', 'to_bool'),  # SDTM MH.MHTERM
    'Do any of your children have congenital malformations or diseases?': ('do_any_of_your_children_have_congenital_malformations_or_diseas', 'to_bool'),  # 
    'Do you consume alcohol?': ('do_you_consume_alcohol', 'to_bool'),  # SDTM MH.MHTERM
    'Do you get it when you walk at an ordinary pace on the level?': ('do_you_get_it_when_you_walk_at_an_ordinary_pace_on_the_level', 'to_bool'),  # SDTM MH.MHTERM
    'Do you get this pain or discomfort when you walk uphill or hurry?': ('do_you_get_this_pain_or_discomfort_when_you_walk_uphill_or_hurr', 'to_bool'),  # SDTM MH.MHTERM
    'Do you have Diabetes?': ('do_you_have_diabetes', 'to_str'),  # 
    'Do you have Erectile dysfunction?': ('do_you_have_erectile_dysfunction', 'to_bool'),  # SDTM MH.MHTERM
    'Do you have Hyperlipidemia?': ('do_you_have_hyperlipidemia', 'to_str'),  # 
    'Do you have Hypertension?': ('do_you_have_hypertension', 'to_bool'),  # SDTM MH.MHTERM
    'Do you have more than one wife?': ('do_you_have_more_than_one_wife', 'to_bool'),  # SDTM MH.MHTERM
    'Do you smoke shisha or cigarettes or both?': ('do_you_smoke_shisha_or_cigarettes_or_both', 'to_bool'),  # SDTM MH.MHTERM
    'Does it go away when you stand still?': ('does_it_go_away_when_you_stand_still', 'to_bool'),  # SDTM MH.MHTERM
    'ECG': ('ecg', 'to_bool'),  # SDTM SV.SVPRTRT
    'ECG - PDF': ('ecg_pdf', 'to_str'),  # SDTM EG.EGATTACH
    'ECG - XML': ('ecg_xml', 'to_str'),  # SDTM EG.EGATTACH
    'ECG / Holter monitoring conclusion': ('ecg_holter_monitoring_conclusion', 'to_str'),  # SDTM EG.EGRESULT
    'ECG Date': ('ecg_date', 'to_date'),  # SDTM EG.EGDTC
    'EF class': ('ef_class', 'to_str'),  # SDTM FA.EFCLS | LOINC:18093-6
    'Echocardiography': ('echocardiography', 'to_bool'),  # SDTM SV.SVPRTRT
    'Ectopic beats': ('ectopic_beats', 'to_bool'),  # SDTM EG.ECTOPIC
    'Electrolytes (Na, K, Ca, Mg ...)': ('electrolytes_na_k_ca_mg', 'to_bool'),  # SDTM SV.SVPRTRT
    'Endocardium (choice=(23) Acute and subacute endocarditis)': ('endocardium_choice_23_acute_and_subacute_endocarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Endocardium (choice=(23.0) Rheumatic diseases of endocardium, valve unspecified)': ('endocardium_choice_23_0_rheumatic_diseases_of_endocardium_valve', 'to_bool'),  # SDTM FA.MHTERM
    'Endocardium (choice=(23.1) Nonrheumatic mitral valve disorders)': ('endocardium_choice_23_1_nonrheumatic_mitral_valve_disorders', 'to_bool'),  # SDTM FA.MHTERM
    'Endocardium (choice=(24) Endocarditis, valve unspecified)': ('endocardium_choice_24_endocarditis_valve_unspecified', 'to_bool'),  # SDTM FA.MHTERM
    'Endocardium (choice=(24.0) Acute rheumatic endocarditis)': ('endocardium_choice_24_0_acute_rheumatic_endocarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Endocardium (choice=(25) Endocarditis and heart valve disorders in diseases classified elsewhere)': ('endocardium_choice_25_endocarditis_and_heart_valve_disorders_in', 'to_bool'),  # SDTM FA.MHTERM
    'Enrollment date': ('enrollment_date', 'to_date'),  # SDTM DM.RFICDTC
    'Exact duration of smoking cessation  * Please select the time unit in the next field (Years, Months, or Days)': ('exact_duration_of_smoking_cessation_please_select_the_time_unit', 'to_float'),  # SDTM SU.DUENDT
    'Extra notes': ('extra_notes', 'to_str'),  # SDTM SV.ADMIN
    'Fasting Blood Glucose': ('fasting_blood_glucose', 'to_float'),  # SDTM LB.FASTGLUC | LOINC:1558-6 | [mg/dL]
    'Fasting blood sugar': ('fasting_blood_sugar', 'to_float'),  # SDTM LB.FASTGLUC | LOINC:1558-6 | [mg/dL]
    'Father origins': ('father_origins', 'to_str'),  # SDTM DM.FTHORIG
    "Father's gov of origin": ('father_s_gov_of_origin', 'to_str'),  # 
    'Findings / Comments  (If there is any changes in parameters related to core clinical examination in recruitment sheet, please go the relevant fields and change accordingly)': ('findings_comments_if_there_is_any_changes_in_parameters_related', 'to_str'),  # SDTM SV.ADMIN
    'For any missing data in this sheet that CANNOT BE ACQUIRED NOW OR IN FUTURE: is it due to POOR ECHOCARDIOGRAPHY WINDOW or TECHNICAL DIFFICULTIES related to this patient? Please specify details in the next box.': ('for_any_missing_data_in_this_sheet_that_cannot_be_acquired_now_', 'to_str'),  # SDTM SV.ADMIN
    'Frequency': ('frequency', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.1': ('frequency_1', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.10': ('frequency_10', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.11': ('frequency_11', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.12': ('frequency_12', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.13': ('frequency_13', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.14': ('frequency_14', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.2': ('frequency_2', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.3': ('frequency_3', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.4': ('frequency_4', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.5': ('frequency_5', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.6': ('frequency_6', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.7': ('frequency_7', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.8': ('frequency_8', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Frequency.9': ('frequency_9', 'to_str'),  # SDTM CM.CMDOSFRQ
    'Further comments': ('further_comments', 'to_str'),  # SDTM SV.ADMIN
    'Further plan': ('further_plan', 'to_str'),  # SDTM SV.ADMIN
    'Further plan details': ('further_plan_details', 'to_str'),  # SDTM SV.ADMIN
    'Further plan document': ('further_plan_document', 'to_str'),  # SDTM SV.ADMIN
    'Gender': ('gender', 'to_str'),  # SDTM DM.SEX | LOINC:46098-0
    'HDL': ('hdl', 'to_float'),  # SDTM LB.HDL | LOINC:2085-9 | [mg/dL]
    'Has anyone in your family (parents, grandparents or siblings) experienced sudden death, MI, stroke, or hospitalization due to heart failure?': ('has_anyone_in_your_family_parents_grandparents_or_siblings_expe', 'to_bool'),  # 
    'Have you been diagnosed with PVD?': ('have_you_been_diagnosed_with_pvd', 'to_bool'),  # SDTM MH.MHTERM
    'Have you been diagnosed with RHD?': ('have_you_been_diagnosed_with_rhd', 'to_bool'),  # SDTM MH.MHTERM
    'Have you been diagnosed with Renal disease?': ('have_you_been_diagnosed_with_renal_disease', 'to_bool'),  # SDTM MH.MHTERM
    'Have you been diagnosed with Respiratory illnesses?': ('have_you_been_diagnosed_with_respiratory_illnesses', 'to_bool'),  # SDTM MH.MHTERM
    'Have you been diagnosed with Rheumatic Fever?': ('have_you_been_diagnosed_with_rheumatic_fever', 'to_bool'),  # SDTM MH.MHTERM
    'Have you been diagnosed with congenital heart disease?': ('have_you_been_diagnosed_with_congenital_heart_disease', 'to_bool'),  # SDTM MH.MHTERM
    'Have you been hospitalized due to heart failure?': ('have_you_been_hospitalized_due_to_heart_failure', 'to_str'),  # 
    'Have you ever been diagnosed with MI?': ('have_you_ever_been_diagnosed_with_mi', 'to_bool'),  # SDTM MH.MHTERM
    'Have you ever had a severe pain across the front of your chest lasting for half an hour or more?': ('have_you_ever_had_a_severe_pain_across_the_front_of_your_chest_', 'to_bool'),  # SDTM MH.MHTERM
    'Have you ever had any pain or discomfort in your chest?': ('have_you_ever_had_any_pain_or_discomfort_in_your_chest', 'to_bool'),  # SDTM MH.MHTERM
    'Have you experienced shortness of breath?': ('have_you_experienced_shortness_of_breath', 'to_bool'),  # SDTM MH.MHTERM
    'Have you had a prior Stroke or TIA?': ('have_you_had_a_prior_stroke_or_tia', 'to_bool'),  # SDTM MH.MHTERM
    'Have you had any other cardiac procedures?': ('have_you_had_any_other_cardiac_procedures', 'to_bool'),  # SDTM MH.MHTERM
    'Have you received Influenza Immunization within a YEAR?': ('have_you_received_influenza_immunization_within_a_year', 'to_bool'),  # SDTM MH.MHTERM
    'Have you undergone a Coronary angioplasty/Stent?': ('have_you_undergone_a_coronary_angioplasty_stent', 'to_bool'),  # SDTM MH.MHTERM
    'Have you undergone a prior CABG?': ('have_you_undergone_a_prior_cabg', 'to_bool'),  # SDTM MH.MHTERM
    'HbA1C': ('hba1c', 'to_float'),  # SDTM LB.HBA1C | LOINC:4548-4 | [%]
    'HbA1c': ('hba1c_2', 'to_float'),  # SDTM LB.HBA1C | LOINC:4548-4 | [%]
    'Heart Failure (choice=(14) Acute Heart Failure)': ('heart_failure_choice_14_acute_heart_failure', 'to_bool'),  # SDTM FA.MHTERM
    'Heart Failure (choice=(15) Left-sided heart failure)': ('heart_failure_choice_15_left_sided_heart_failure', 'to_bool'),  # SDTM FA.MHTERM
    'Heart Failure (choice=(15.0) Heart failure with reduced ejection fraction (HFrEF) (EF?40%))': ('heart_failure_choice_15_0_heart_failure_with_reduced_ejection_f', 'to_bool'),  # SDTM FA.MHTERM
    'Heart Failure (choice=(15.1) Heart failure with preserved ejection fraction (HFpEF) (EF?50%))': ('heart_failure_choice_15_1_heart_failure_with_preserved_ejection', 'to_bool'),  # SDTM FA.MHTERM
    'Heart Failure (choice=(15.2) Heart failure with borderline ejection fraction (HFpEF) (EF=41-49%))': ('heart_failure_choice_15_2_heart_failure_with_borderline_ejectio', 'to_bool'),  # SDTM FA.MHTERM
    'Heart Failure (choice=(16) Right-sided heart failure)': ('heart_failure_choice_16_right_sided_heart_failure', 'to_bool'),  # SDTM FA.MHTERM
    'Heart rate': ('heart_rate', 'to_float'),  # SDTM VS.HR | LOINC:8867-4 | [/min]
    'Height in cm': ('height_in_cm', 'to_float'),  # SDTM VS.HEIGHT | LOINC:8302-2 | [cm]
    'Hematocrit': ('hematocrit', 'to_float'),  # SDTM LB.HCT | LOINC:4544-3 | [%]
    'Hemoglobin': ('hemoglobin', 'to_float'),  # SDTM LB.HGB | LOINC:718-7 | [g/dL]
    'Hip circumference in cm': ('hip_circumference_in_cm', 'to_float'),  # SDTM VS.HIPCIR | LOINC:62409-8 | [cm]
    'Holter': ('holter', 'to_bool'),  # SDTM SV.SVPRTRT
    'Household identifier': ('household_identifier', 'to_str'),  # SDTM DM.HHID
    'How soon?': ('how_soon', 'to_str'),  # SDTM SV.ADMIN
    'Hypertensive diseases (choice=(39) Essential (primary) hypertension)': ('hypertensive_diseases_choice_39_essential_primary_hypertension', 'to_bool'),  # SDTM MH.MHTERM
    'Hypertensive diseases (choice=(39.0) Arterial hypertension)': ('hypertensive_diseases_choice_39_0_arterial_hypertension', 'to_bool'),  # SDTM MH.MHTERM
    'Hypertensive diseases (choice=(40) Hypertensive heart disease)': ('hypertensive_diseases_choice_40_hypertensive_heart_disease', 'to_bool'),  # SDTM MH.MHTERM
    'Hypertensive diseases (choice=(41) Hypertensive renal disease)': ('hypertensive_diseases_choice_41_hypertensive_renal_disease', 'to_bool'),  # SDTM MH.MHTERM
    'Hypertensive diseases (choice=(41.0) Hypertensive nephropathy)': ('hypertensive_diseases_choice_41_0_hypertensive_nephropathy', 'to_bool'),  # SDTM MH.MHTERM
    'Hypertensive diseases (choice=(42) Hypertensive heart disease and Hypertensive renal disease)': ('hypertensive_diseases_choice_42_hypertensive_heart_disease_and_', 'to_bool'),  # SDTM MH.MHTERM
    'Hypertensive diseases (choice=(43) Secondary hypertension)': ('hypertensive_diseases_choice_43_secondary_hypertension', 'to_bool'),  # SDTM MH.MHTERM
    'Hypertensive diseases (choice=(43.0) Renovascular hypertension)': ('hypertensive_diseases_choice_43_0_renovascular_hypertension', 'to_bool'),  # SDTM MH.MHTERM
    'Hypotensive diseases (choice=(44) Idiopathic hypotension)': ('hypotensive_diseases_choice_44_idiopathic_hypotension', 'to_bool'),  # SDTM MH.MHTERM
    'Hypotensive diseases (choice=(45) Orthostatic hypotension)': ('hypotensive_diseases_choice_45_orthostatic_hypotension', 'to_bool'),  # SDTM MH.MHTERM
    'Hypotensive diseases (choice=(46) Hypotension due to drugs)': ('hypotensive_diseases_choice_46_hypotension_due_to_drugs', 'to_bool'),  # SDTM MH.MHTERM
    'Hypotensive diseases (choice=(47) Hypotension, unspecified)': ('hypotensive_diseases_choice_47_hypotension_unspecified', 'to_bool'),  # SDTM MH.MHTERM
    'IMT - left in mm': ('imt_left_in_mm', 'to_float'),  # SDTM VS.CARIMTL | LOINC:24889-5 | [mm]
    'IMT - right in mm': ('imt_right_in_mm', 'to_float'),  # SDTM VS.CARIMTR | LOINC:24890-3 | [mm]
    'INR': ('inr', 'to_float'),  # SDTM LB.INR | LOINC:6301-6 | [1]
    'If father is Egyptian, please specify city': ('if_father_is_egyptian_please_specify_city', 'to_str'),  # SDTM SV.ADMIN
    'If father is non-Egyptian, please specify': ('if_father_is_non_egyptian_please_specify', 'to_str'),  # SDTM SV.ADMIN
    'If mother is Egyptian, please specify city/': ('if_mother_is_egyptian_please_specify_city', 'to_str'),  # SDTM DM.CHLDCITY
    'If mother is non-Egyptian, please specify': ('if_mother_is_non_egyptian_please_specify', 'to_str'),  # SDTM SV.ADMIN
    'If other, specify': ('if_other_specify', 'to_str'),  # SDTM SV.ADMIN
    'If yes,  age of onset': ('if_yes_age_of_onset', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please note MRN': ('if_yes_please_note_mrn', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify': ('if_yes_please_specify', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify age of onset': ('if_yes_please_specify_age_of_onset', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify age of onset, and details.': ('if_yes_please_specify_age_of_onset_and_details', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify age of onset.1': ('if_yes_please_specify_age_of_onset_1', 'to_str'),  # 
    'If yes, please specify age of onset.2': ('if_yes_please_specify_age_of_onset_2', 'to_str'),  # 
    'If yes, please specify age of onset.3': ('if_yes_please_specify_age_of_onset_3', 'to_str'),  # 
    'If yes, please specify age of onset.4': ('if_yes_please_specify_age_of_onset_4', 'to_str'),  # 
    'If yes, please specify date': ('if_yes_please_specify_date', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify date of CABG': ('if_yes_please_specify_date_of_cabg', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify details, and age of onset': ('if_yes_please_specify_details_and_age_of_onset', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify disease': ('if_yes_please_specify_disease', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify number and date of hospitalizations': ('if_yes_please_specify_number_and_date_of_hospitalizations', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify the highest degree obtained': ('if_yes_please_specify_the_highest_degree_obtained', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify type': ('if_yes_please_specify_type', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify type and age of onset': ('if_yes_please_specify_type_and_age_of_onset', 'to_str'),  # SDTM SV.ADMIN
    'If yes, please specify type and date': ('if_yes_please_specify_type_and_date', 'to_str'),  # SDTM SV.ADMIN
    'If yes, stenosis % (LT)': ('if_yes_stenosis_lt', 'to_str'),  # SDTM SV.ADMIN
    'If yes, stenosis % (RT)': ('if_yes_stenosis_rt', 'to_str'),  # SDTM SV.ADMIN
    'In general, how would you rate your health today?': ('in_general_how_would_you_rate_your_health_today', 'to_str'),  # SDTM SV.ADMIN
    'Intervention required': ('intervention_required', 'to_str'),  # SDTM SV.ADMIN
    'Ischaemic heart diseases (choice=(10) Complications following acute myocardial infarction)': ('ischaemic_heart_diseases_choice_10_complications_following_acut', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(10.0) Haemopericardium)': ('ischaemic_heart_diseases_choice_10_0_haemopericardium', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(10.1) Atrial septal defect)': ('ischaemic_heart_diseases_choice_10_1_atrial_septal_defect', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(10.2) Ventricular septal defect)': ('ischaemic_heart_diseases_choice_10_2_ventricular_septal_defect', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(10.3) Rupture of cardiac wall without haemopericardium)': ('ischaemic_heart_diseases_choice_10_3_rupture_of_cardiac_wall_wi', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(10.4) Rupture of chordae tendineae)': ('ischaemic_heart_diseases_choice_10_4_rupture_of_chordae_tendine', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(10.5) Rupture of papillary muscle)': ('ischaemic_heart_diseases_choice_10_5_rupture_of_papillary_muscl', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(10.6) Thrombosis of atrium, auricular appendage, and ventricle)': ('ischaemic_heart_diseases_choice_10_6_thrombosis_of_atrium_auric', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(10.7) Other current complications following acute MI)': ('ischaemic_heart_diseases_choice_10_7_other_current_complication', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(12) Other acute ischaemic heart diseases)': ('ischaemic_heart_diseases_choice_12_other_acute_ischaemic_heart_', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(12.0) Coronary thrombosis not resulting in myocardial infarction)': ('ischaemic_heart_diseases_choice_12_0_coronary_thrombosis_not_re', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(12.1) Dresslers syndrome)': ('ischaemic_heart_diseases_choice_12_1_dresslers_syndrome', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(13) Chronic ischaemic heart disease)': ('ischaemic_heart_diseases_choice_13_chronic_ischaemic_heart_dise', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(13.0) Atherosclerotic cardiovascular disease)': ('ischaemic_heart_diseases_choice_13_0_atherosclerotic_cardiovasc', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(13.1) Atherosclerotic heart disease)': ('ischaemic_heart_diseases_choice_13_1_atherosclerotic_heart_dise', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(13.2) Old myocardial infarction)': ('ischaemic_heart_diseases_choice_13_2_old_myocardial_infarction', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(13.3) Aneurysm of heart)': ('ischaemic_heart_diseases_choice_13_3_aneurysm_of_heart', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(13.4) Coronary artery aneurysm)': ('ischaemic_heart_diseases_choice_13_4_coronary_artery_aneurysm', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(13.5) Ischaemic cardiomyopathy)': ('ischaemic_heart_diseases_choice_13_5_ischaemic_cardiomyopathy', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(13.6) Silent myocardial ischaemia)': ('ischaemic_heart_diseases_choice_13_6_silent_myocardial_ischaemi', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(13.7) Other forms of chronic ischaemic heart disease)': ('ischaemic_heart_diseases_choice_13_7_other_forms_of_chronic_isc', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(9) Acute coronary syndrome)': ('ischaemic_heart_diseases_choice_9_acute_coronary_syndrome', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(9.0) Non-ST-elevation acute coronary syndrome (NSTE-ACS))': ('ischaemic_heart_diseases_choice_9_0_non_st_elevation_acute_coro', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=(9.1) ST-elevation acute coronary syndrome (STE-ACS))': ('ischaemic_heart_diseases_choice_9_1_st_elevation_acute_coronary', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=----- Non-ST-Elevation myocardial infarct (NSTEMI))': ('ischaemic_heart_diseases_choice_non_st_elevation_myocardial_inf', 'to_bool'),  # SDTM FA.MHTERM
    'Ischaemic heart diseases (choice=----- Unstable Angina)': ('ischaemic_heart_diseases_choice_unstable_angina', 'to_bool'),  # SDTM FA.MHTERM
    'K': ('k', 'to_float'),  # SDTM LB.K | LOINC:2823-3 | [mmol/L]
    'Kidney functions': ('kidney_functions', 'to_bool'),  # SDTM SV.SVPRTRT
    'LA diameter - PLAX': ('la_diameter_plax', 'to_float'),  # SDTM FA.LADIAM | LOINC:18035-7 | [mm]
    "LA volume - Simpson's": ('la_volume_simpson_s', 'to_float'),  # SDTM FA.LAVOL | LOINC:34655-2 | [mL]
    'LDL': ('ldl', 'to_float'),  # SDTM LB.LDL | LOINC:2089-1 | [mg/dL]
    'LV diastolic dysfunction': ('lv_diastolic_dysfunction', 'to_str'),  # SDTM FA.LVDDI | LOINC:34552-1
    'LV size': ('lv_size', 'to_float'),  # SDTM FA.LVSIZE | LOINC:29430-6 | [mm]
    'LVEDD': ('lvedd', 'to_float'),  # SDTM FA.LVEDD | LOINC:18026-6 | [mm]
    'LVEF - M mode': ('lvef_m_mode', 'to_float'),  # SDTM FA.EF
    "LVEF - Simpson's": ('lvef_simpson_s', 'to_float'),  # SDTM FA.EF
    'LVEF - Visual': ('lvef_visual', 'to_float'),  # SDTM FA.EF
    'LVESD': ('lvesd', 'to_float'),  # SDTM FA.LVESD | LOINC:18150-4 | [mm]
    'LVH': ('lvh', 'to_bool'),  # SDTM FA.LVH
    'LVH.1': ('lvh_1', 'to_str'),  # 
    'Left anterior tibial ABI': ('left_anterior_tibial_abi', 'to_float'),  # SDTM VS.LABIAT | LOINC:37399-3 | [1]
    'Left anterior tibial pressure': ('left_anterior_tibial_pressure', 'to_float'),  # SDTM VS.LATP | [mm[Hg]]
    'Left atrial size': ('left_atrial_size', 'to_float'),  # SDTM FA.LASIZE | LOINC:29430-6 | [mm]
    'Left posterior tibial ABI': ('left_posterior_tibial_abi', 'to_float'),  # SDTM VS.LTABI | LOINC:8641-0 | [1]
    'Left posterior tibial pressure': ('left_posterior_tibial_pressure', 'to_float'),  # SDTM VS.LPTP | [mm[Hg]]
    'Life Sciences re-sampling': ('life_sciences_re_sampling', 'to_str'),  # SDTM SV.ADMIN
    'Lifetime ASCVD risk (%)': ('lifetime_ascvd_risk', 'to_float'),  # [%]
    'Lipid profile': ('lipid_profile', 'to_bool'),  # SDTM SV.SVPRTRT
    'Liver functions': ('liver_functions', 'to_bool'),  # SDTM SV.SVPRTRT
    'Lower limb Duplex': ('lower_limb_duplex', 'to_bool'),  # SDTM SV.SVPRTRT
    'MCH': ('mch', 'to_float'),  # SDTM LB.MCH | LOINC:785-6 | [pg]
    'MCHC': ('mchc', 'to_float'),  # SDTM LB.MCHC | LOINC:786-4 | [g/dL]
    'MCV': ('mcv', 'to_float'),  # SDTM LB.MCV | LOINC:787-2 | [fL]
    'MR': ('mr', 'to_str'),  # SDTM FA.MR
    'MRI - Specify': ('mri_specify', 'to_str'),  # SDTM SV.ADMIN
    'MRN (AHC)': ('mrn_ahc', 'to_str'),  # SDTM SV.ADMIN
    'MRN (BU)': ('mrn_bu', 'to_str'),  # SDTM SV.ADMIN
    'MS': ('ms', 'to_str'),  # SDTM FA.MS
    'Major category (choice=CHD)': ('major_category_choice_chd', 'to_bool'),  # SDTM FA.MAJCAT
    'Major category (choice=Cardiomyopathy)': ('major_category_choice_cardiomyopathy', 'to_bool'),  # SDTM FA.MAJCAT
    'Major category (choice=HF)': ('major_category_choice_hf', 'to_bool'),  # SDTM FA.MAJCAT
    'Major category (choice=IHD)': ('major_category_choice_ihd', 'to_bool'),  # SDTM FA.MAJCAT
    'Major category (choice=None)': ('major_category_choice_none', 'to_bool'),  # SDTM FA.MAJCAT
    'Major category (choice=Other CV disease)': ('major_category_choice_other_cv_disease', 'to_bool'),  # SDTM FA.MAJCAT
    'Major category (choice=Other co-morbdidites / risk factors)': ('major_category_choice_other_co_morbdidites_risk_factors', 'to_bool'),  # SDTM FA.MAJCAT
    'Major category (choice=PHT)': ('major_category_choice_pht', 'to_bool'),  # SDTM FA.MAJCAT
    'Major category (choice=RHD)': ('major_category_choice_rhd', 'to_bool'),  # SDTM FA.MAJCAT
    'Major category (choice=Valvular)': ('major_category_choice_valvular', 'to_bool'),  # SDTM FA.MAJCAT
    'Mg': ('mg', 'to_float'),  # SDTM LB.MG | LOINC:2601-3 | [mg/dL]
    'Midventricular - Anterior': ('midventricular_anterior', 'to_int'),  # 
    'Midventricular - Anterolateral': ('midventricular_anterolateral', 'to_int'),  # 
    'Midventricular - Anteroseptal': ('midventricular_anteroseptal', 'to_int'),  # 
    'Midventricular - Inferior': ('midventricular_inferior', 'to_int'),  # 
    'Midventricular - Inferolateral': ('midventricular_inferolateral', 'to_int'),  # 
    'Midventricular - Inferoseptal': ('midventricular_inferoseptal', 'to_int'),  # 
    'Moderate or severe valvular lesion': ('moderate_or_severe_valvular_lesion', 'to_bool'),  # SDTM FA.VALVLSN
    'Mother origins': ('mother_origins', 'to_str'),  # SDTM DM.MTHORIG
    "Mother's gov of origin": ('mother_s_gov_of_origin', 'to_str'),  # 
    'Myocardial perfusion imaging': ('myocardial_perfusion_imaging', 'to_bool'),  # SDTM SV.SVPRTRT
    'Myocardium / Cardiomyopathy (choice=(17) Acute myocarditis)': ('myocardium_cardiomyopathy_choice_17_acute_myocarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(18) Chronic myocarditis)': ('myocardium_cardiomyopathy_choice_18_chronic_myocarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(19) Myocarditis in diseases classified elsewhere)': ('myocardium_cardiomyopathy_choice_19_myocarditis_in_diseases_cla', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(19.0)  Rheumatic myocarditis)': ('myocardium_cardiomyopathy_choice_19_0_rheumatic_myocarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(20) Myocardial degeneration)': ('myocardium_cardiomyopathy_choice_20_myocardial_degeneration', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(21) Cardiomyopathy)': ('myocardium_cardiomyopathy_choice_21_cardiomyopathy', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(21.0) Dilated cardiomyopathy)': ('myocardium_cardiomyopathy_choice_21_0_dilated_cardiomyopathy', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(21.1) Obstructive hypertrophy cardiomyopathy)': ('myocardium_cardiomyopathy_choice_21_1_obstructive_hypertrophy_c', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(21.2) Other hypertrophic cardiomyopathy)': ('myocardium_cardiomyopathy_choice_21_2_other_hypertrophic_cardio', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(21.3) Endomyocardial (eosinophilic) disease)': ('myocardium_cardiomyopathy_choice_21_3_endomyocardial_eosinophil', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(21.4) Endocardial fibroelastosis)': ('myocardium_cardiomyopathy_choice_21_4_endocardial_fibroelastosi', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(21.5) Other restrictive cardiomyopathy)': ('myocardium_cardiomyopathy_choice_21_5_other_restrictive_cardiom', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(21.6) Alcoholic cardiomyopathy)': ('myocardium_cardiomyopathy_choice_21_6_alcoholic_cardiomyopathy', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(21.8) Other cardiomyopathies)': ('myocardium_cardiomyopathy_choice_21_8_other_cardiomyopathies', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=(22) Cardiomyopathy in diseases classified elsewhere)': ('myocardium_cardiomyopathy_choice_22_cardiomyopathy_in_diseases_', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=---- Arrhythmogenic right ventricular dysplasia)': ('myocardium_cardiomyopathy_choice_arrhythmogenic_right_ventricul', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=---- Endomyocardial (tropical) fibrosis)': ('myocardium_cardiomyopathy_choice_endomyocardial_tropical_fibros', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=---- Eosinophilic myocarditis)': ('myocardium_cardiomyopathy_choice_eosinophilic_myocarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Myocardium / Cardiomyopathy (choice=---- Loefflers endocarditis)': ('myocardium_cardiomyopathy_choice_loefflers_endocarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Myxomatous valve disease': ('myxomatous_valve_disease', 'to_str'),  # SDTM FA.MYXVALV
    'Myxomatous valve(s) (choice=Aortic)': ('myxomatous_valve_s_choice_aortic', 'to_bool'),  # 
    'Myxomatous valve(s) (choice=Mitral)': ('myxomatous_valve_s_choice_mitral', 'to_bool'),  # 
    'Myxomatous valve(s) (choice=Pulmonary)': ('myxomatous_valve_s_choice_pulmonary', 'to_bool'),  # 
    'Myxomatous valve(s) (choice=Tricuspid)': ('myxomatous_valve_s_choice_tricuspid', 'to_bool'),  # 
    'Na': ('na', 'to_float'),  # LOINC:2951-2 | [mmol/L]
    'Name': ('name', 'to_str'),  # SDTM CM.CMTRT
    'Name.1': ('name_1', 'to_str'),  # SDTM CM.CMTRT
    'Name.10': ('name_10', 'to_str'),  # SDTM CM.CMTRT
    'Name.11': ('name_11', 'to_str'),  # SDTM CM.CMTRT
    'Name.12': ('name_12', 'to_str'),  # SDTM CM.CMTRT
    'Name.13': ('name_13', 'to_str'),  # SDTM CM.CMTRT
    'Name.14': ('name_14', 'to_str'),  # SDTM CM.CMTRT
    'Name.2': ('name_2', 'to_str'),  # SDTM CM.CMTRT
    'Name.3': ('name_3', 'to_str'),  # SDTM CM.CMTRT
    'Name.4': ('name_4', 'to_str'),  # SDTM CM.CMTRT
    'Name.5': ('name_5', 'to_str'),  # SDTM CM.CMTRT
    'Name.6': ('name_6', 'to_str'),  # SDTM CM.CMTRT
    'Name.7': ('name_7', 'to_str'),  # SDTM CM.CMTRT
    'Name.8': ('name_8', 'to_str'),  # SDTM CM.CMTRT
    'Name.9': ('name_9', 'to_str'),  # SDTM CM.CMTRT
    'Native AV morphology': ('native_av_morphology', 'to_str'),  # SDTM FA.AVMORPH
    'Optimal ASCVD Risk': ('optimal_ascvd_risk', 'to_float'),  # SDTM FA.ASCVDOPT | [%]
    'Other co-morbidities  / risk factors (choice=Diabetes mellitus)': ('other_co_morbidities_risk_factors_choice_diabetes_mellitus', 'to_bool'),  # SDTM MH.MHTERM
    'Other co-morbidities  / risk factors (choice=Dyslipidemia)': ('other_co_morbidities_risk_factors_choice_dyslipidemia', 'to_bool'),  # SDTM MH.MHTERM
    'Other co-morbidities  / risk factors (choice=Familial hypercholesterolemia)': ('other_co_morbidities_risk_factors_choice_familial_hypercholeste', 'to_bool'),  # SDTM MH.MHTERM
    'Other co-morbidities  / risk factors (choice=Hypertension)': ('other_co_morbidities_risk_factors_choice_hypertension', 'to_bool'),  # SDTM MH.MHTERM
    'Other co-morbidities  / risk factors (choice=None)': ('other_co_morbidities_risk_factors_choice_none', 'to_bool'),  # SDTM MH.MHTERM
    'Other co-morbidities  / risk factors (choice=Other)': ('other_co_morbidities_risk_factors_choice_other', 'to_bool'),  # SDTM MH.MHTERM
    'Other echocardiographic findings': ('other_echocardiographic_findings', 'to_str'),  # SDTM FA.FAOTHER
    'Other ethnicity': ('other_ethnicity', 'to_str'),  # SDTM DM.ETHNIC
    'Other laboratory results to report': ('other_laboratory_results_to_report', 'to_str'),  # SDTM SV.ADMIN
    'Others imaging modality- Specify': ('others_imaging_modality_specify', 'to_str'),  # SDTM SV.ADMIN
    'Others lab work - Specify': ('others_lab_work_specify', 'to_str'),  # SDTM SV.ADMIN
    'PASP': ('pasp', 'to_float'),  # SDTM FA.PASP | LOINC:33453-2 | [mm[Hg]]
    'PR': ('pr', 'to_str'),  # SDTM FA.PR
    'PS': ('ps', 'to_str'),  # SDTM FA.PS
    'PWT': ('pwt', 'to_float'),  # SDTM FA.LVPWD | LOINC:18090-2 | [mm]
    "Participant's Name": ('participant_s_name', 'to_str'),  # SDTM DM.ADMIN
    'Pedigree': ('pedigree', 'to_str'),  # SDTM SV.ADMIN
    'Pericardium (choice=(26) Acute pericarditis)': ('pericardium_choice_26_acute_pericarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=(26.0) Acute rheumatic pericarditis)': ('pericardium_choice_26_0_acute_rheumatic_pericarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=(27) Chronic pericarditis)': ('pericardium_choice_27_chronic_pericarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=(27.0) Chronic adhesive pericarditis)': ('pericardium_choice_27_0_chronic_adhesive_pericarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=(27.1) Chronic constrictive pericarditis)': ('pericardium_choice_27_1_chronic_constrictive_pericarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=(27.2) Chronic rheumatic pericarditis)': ('pericardium_choice_27_2_chronic_rheumatic_pericarditis', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=(28) Other diseases of pericardium)': ('pericardium_choice_28_other_diseases_of_pericardium', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=(28.0) Haemopericardium, not elsewhere classified)': ('pericardium_choice_28_0_haemopericardium_not_elsewhere_classifi', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=(28.1) Pericardial effusion (noninflammatory))': ('pericardium_choice_28_1_pericardial_effusion_noninflammatory', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=(29) Other specified diseases of pericardium)': ('pericardium_choice_29_other_specified_diseases_of_pericardium', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=(29.0) Cardiac tamponade)': ('pericardium_choice_29_0_cardiac_tamponade', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=(30) Pericarditis in diseases classified elsewhere)': ('pericardium_choice_30_pericarditis_in_diseases_classified_elsew', 'to_bool'),  # SDTM FA.MHTERM
    'Pericardium (choice=Normal)': ('pericardium_choice_normal', 'to_bool'),  # 
    'Pericardium (choice=calcified)': ('pericardium_choice_calcified', 'to_bool'),  # 
    'Pericardium (choice=effusion)': ('pericardium_choice_effusion', 'to_bool'),  # 
    'Platelet count': ('platelet_count', 'to_float'),  # SDTM LB.PLAT | LOINC:777-3 | [10*3/uL]
    'Prescription document by BHS clinic': ('prescription_document_by_bhs_clinic', 'to_str'),  # SDTM SV.ADMIN
    'Present, or most recent past, occupation': ('present_or_most_recent_past_occupation', 'to_str'),  # SDTM SC.SCTEST
    'Previous Patient at AHC': ('previous_patient_at_ahc', 'to_bool'),  # SDTM SV.ADMIN
    'Pulmonary hypertension': ('pulmonary_hypertension', 'to_bool'),  # SDTM FA.PHTN | LOINC:8867-4
    'Pulmonary vascular disease  (choice=(31) Pulmonary hypertension)': ('pulmonary_vascular_disease_choice_31_pulmonary_hypertension', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=(31.0) Pulmonary arterial hypertension)': ('pulmonary_vascular_disease_choice_31_0_pulmonary_arterial_hyper', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=(31.1) Pulmonary hypertension due to left-heart disease (pulmonary venous hypertension))': ('pulmonary_vascular_disease_choice_31_1_pulmonary_hypertension_d', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=(31.2) Pulmonary hypertension associated with respiratory or chronic hypoxic lung disease)': ('pulmonary_vascular_disease_choice_31_2_pulmonary_hypertension_a', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=(32) Pulmonary embolism)': ('pulmonary_vascular_disease_choice_32_pulmonary_embolism', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=(32.3) Chronic thromboembolic/ embolic pulmonary hypertension)': ('pulmonary_vascular_disease_choice_32_3_chronic_thromboembolic_e', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=(32.4) Pulmonary hypertension from unclear mechanisms)': ('pulmonary_vascular_disease_choice_32_4_pulmonary_hypertension_f', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=---- COPD / interstitial lung disease)': ('pulmonary_vascular_disease_choice_copd_interstitial_lung_diseas', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=---- Chronic kindey failure)': ('pulmonary_vascular_disease_choice_chronic_kindey_failure', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=---- Congenital heart disease)': ('pulmonary_vascular_disease_choice_congenital_heart_disease', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=---- Idiopathic / Primary)': ('pulmonary_vascular_disease_choice_idiopathic_primary', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=---- LV Systolic dysfunction)': ('pulmonary_vascular_disease_choice_lv_systolic_dysfunction', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=---- LV diastolic dysfunction)': ('pulmonary_vascular_disease_choice_lv_diastolic_dysfunction', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=---- Metabolic disorder)': ('pulmonary_vascular_disease_choice_metabolic_disorder', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=---- Obstructive sleep apnea)': ('pulmonary_vascular_disease_choice_obstructive_sleep_apnea', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=---- Secondary to systemic disorders)': ('pulmonary_vascular_disease_choice_secondary_to_systemic_disorde', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=---- Systemic disorder)': ('pulmonary_vascular_disease_choice_systemic_disorder', 'to_bool'),  # SDTM FA.MHTERM
    'Pulmonary vascular disease  (choice=---- Valvular heart Disease)': ('pulmonary_vascular_disease_choice_valvular_heart_disease', 'to_bool'),  # SDTM FA.MHTERM
    'QRS duration': ('qrs_duration', 'to_float'),  # SDTM EG.QRSDUR | LOINC:8625-6 | [ms]
    'QRS width >= 120 ms': ('qrs_width_120_ms', 'to_bool'),  # SDTM EG.EGQRSWDE | LOINC:8633-7
    'QT interval': ('qt_interval', 'to_float'),  # SDTM EG.QT | LOINC:8634-8 | [ms]
    'RBCs': ('rbcs', 'to_float'),  # SDTM LB.RBC | LOINC:789-8 | [10*6/uL]
    'RDW': ('rdw', 'to_float'),  # SDTM LB.RDW | LOINC:788-0 | [%]
    'RHD-affected valves (choice=Aortic)': ('rhd_affected_valves_choice_aortic', 'to_bool'),  # 
    'RHD-affected valves (choice=Mitral)': ('rhd_affected_valves_choice_mitral', 'to_bool'),  # 
    'RHD-affected valves (choice=Pulmonary)': ('rhd_affected_valves_choice_pulmonary', 'to_bool'),  # 
    'RHD-affected valves (choice=Tricuspid)': ('rhd_affected_valves_choice_tricuspid', 'to_bool'),  # 
    'RV diameters - basal': ('rv_diameters_basal', 'to_float'),  # SDTM FA.RVDIAM
    'RV diameters - longitudinal': ('rv_diameters_longitudinal', 'to_float'),  # SDTM FA.RVDIAM
    'RV diameters - mild': ('rv_diameters_mild', 'to_float'),  # SDTM FA.RVDIAM
    'RV size': ('rv_size', 'to_float'),  # SDTM FA.RVSIZE | LOINC:29430-6 | [mm]
    'RWMA Index': ('rwma_index', 'to_float'),  # SDTM FA.RWMAIDX | [1]
    'RWMA Score': ('rwma_score', 'to_float'),  # [1]
    'Random Blood Glucose': ('random_blood_glucose', 'to_float'),  # SDTM LB.GLUC | LOINC:2345-7 | [mg/dL]
    'Record ID': ('record_id', 'to_str'),  # 
    'Refer to AHC clinic - BMV': ('refer_to_ahc_clinic_bmv', 'to_str'),  # SDTM SV.ADMIN
    'Refer to AHC clinic - EP': ('refer_to_ahc_clinic_ep', 'to_str'),  # SDTM SV.ADMIN
    'Refer to AHC clinic - GUCH': ('refer_to_ahc_clinic_guch', 'to_str'),  # SDTM SV.ADMIN
    'Refer to AHC clinic - General': ('refer_to_ahc_clinic_general', 'to_str'),  # SDTM SV.ADMIN
    'Refer to AHC clinic - Heart failure': ('refer_to_ahc_clinic_heart_failure', 'to_str'),  # SDTM SV.ADMIN
    'Refer to AHC clinic - LVAD': ('refer_to_ahc_clinic_lvad', 'to_str'),  # SDTM SV.ADMIN
    'Refer to AHC clinic - Other - Specify': ('refer_to_ahc_clinic_other_specify', 'to_str'),  # SDTM SV.ADMIN
    'Refer to AHC clinic - Pulmonary': ('refer_to_ahc_clinic_pulmonary', 'to_str'),  # SDTM SV.ADMIN
    'Refer to AHC clinic - TAVI': ('refer_to_ahc_clinic_tavi', 'to_str'),  # SDTM SV.ADMIN
    'Refer to another speciality clinic - Specify': ('refer_to_another_speciality_clinic_specify', 'to_str'),  # SDTM SV.ADMIN
    'Regional wall motion abnormalities': ('regional_wall_motion_abnormalities', 'to_bool'),  # SDTM FA.RWMAYN
    'Relative 1 age at event': ('relative_1_age_at_event', 'to_int'),  # SDTM MH.MHAGE
    'Relative 1 event': ('relative_1_event', 'to_str'),  # SDTM MH.MHEVENT
    'Relative 1 gender': ('relative_1_gender', 'to_str'),  # SDTM MH.MHSEX
    'Relative 1 relation': ('relative_1_relation', 'to_str'),  # SDTM MH.MHREL
    'Relative 10 age at event': ('relative_10_age_at_event', 'to_int'),  # SDTM MH.MHAGE
    'Relative 10 event': ('relative_10_event', 'to_str'),  # SDTM MH.MHEVENT
    'Relative 10 gender': ('relative_10_gender', 'to_str'),  # SDTM MH.MHSEX
    'Relative 10 relation': ('relative_10_relation', 'to_str'),  # SDTM MH.MHREL
    'Relative 2 age at event': ('relative_2_age_at_event', 'to_int'),  # SDTM MH.MHAGE
    'Relative 2 event': ('relative_2_event', 'to_str'),  # SDTM MH.MHEVENT
    'Relative 2 gender': ('relative_2_gender', 'to_str'),  # SDTM MH.MHSEX
    'Relative 2 relation': ('relative_2_relation', 'to_str'),  # SDTM MH.MHREL
    'Relative 3 age at event': ('relative_3_age_at_event', 'to_int'),  # SDTM MH.MHAGE
    'Relative 3 event': ('relative_3_event', 'to_str'),  # SDTM MH.MHEVENT
    'Relative 3 gender': ('relative_3_gender', 'to_str'),  # SDTM MH.MHSEX
    'Relative 3 relation': ('relative_3_relation', 'to_str'),  # SDTM MH.MHREL
    'Relative 4 age at event': ('relative_4_age_at_event', 'to_int'),  # SDTM MH.MHAGE
    'Relative 4 event': ('relative_4_event', 'to_str'),  # SDTM MH.MHEVENT
    'Relative 4 gender': ('relative_4_gender', 'to_str'),  # SDTM MH.MHSEX
    'Relative 4 relation': ('relative_4_relation', 'to_str'),  # SDTM MH.MHREL
    'Relative 5 age at event': ('relative_5_age_at_event', 'to_int'),  # SDTM MH.MHAGE
    'Relative 5 event': ('relative_5_event', 'to_str'),  # SDTM MH.MHEVENT
    'Relative 5 gender': ('relative_5_gender', 'to_str'),  # SDTM MH.MHSEX
    'Relative 5 relation': ('relative_5_relation', 'to_str'),  # SDTM MH.MHREL
    'Relative 6 age at event': ('relative_6_age_at_event', 'to_int'),  # SDTM MH.MHAGE
    'Relative 6 event': ('relative_6_event', 'to_str'),  # SDTM MH.MHEVENT
    'Relative 6 gender': ('relative_6_gender', 'to_str'),  # SDTM MH.MHSEX
    'Relative 6 relation': ('relative_6_relation', 'to_str'),  # SDTM MH.MHREL
    'Relative 7 age at event': ('relative_7_age_at_event', 'to_int'),  # SDTM MH.MHAGE
    'Relative 7 event': ('relative_7_event', 'to_str'),  # SDTM MH.MHEVENT
    'Relative 7 gender': ('relative_7_gender', 'to_str'),  # SDTM MH.MHSEX
    'Relative 7 relation': ('relative_7_relation', 'to_str'),  # SDTM MH.MHREL
    'Relative 8 age at event': ('relative_8_age_at_event', 'to_int'),  # SDTM MH.MHAGE
    'Relative 8 event': ('relative_8_event', 'to_str'),  # SDTM MH.MHEVENT
    'Relative 8 gender': ('relative_8_gender', 'to_str'),  # SDTM MH.MHSEX
    'Relative 8 relation': ('relative_8_relation', 'to_str'),  # SDTM MH.MHREL
    'Relative 9 age at event': ('relative_9_age_at_event', 'to_int'),  # SDTM MH.MHAGE
    'Relative 9 event': ('relative_9_event', 'to_str'),  # SDTM MH.MHEVENT
    'Relative 9 gender': ('relative_9_gender', 'to_str'),  # SDTM MH.MHSEX
    'Relative 9 relation': ('relative_9_relation', 'to_str'),  # SDTM MH.MHREL
    'Renal Duplex': ('renal_duplex', 'to_bool'),  # SDTM SV.SVPRTRT
    'Results': ('results', 'to_str'),  # SDTM SV.ADMIN
    'Rheumatic valvular heart disease': ('rheumatic_valvular_heart_disease', 'to_bool'),  # SDTM MH.MHTERM
    'Rhythm in ECG': ('rhythm_in_ecg', 'to_str'),  # SDTM EG.EGRHY | LOINC:8884-9
    'Right anterior tibial ABI': ('right_anterior_tibial_abi', 'to_float'),  # SDTM VS.RABIAT | LOINC:37399-3 | [1]
    'Right anterior tibial pressure': ('right_anterior_tibial_pressure', 'to_float'),  # SDTM VS.RATP | [mm[Hg]]
    'Right posterior tibial ABI': ('right_posterior_tibial_abi', 'to_float'),  # SDTM VS.RABIAT | LOINC:37399-3 | [1]
    'Right posterior tibial pressure': ('right_posterior_tibial_pressure', 'to_float'),  # SDTM VS.RPTP | [mm[Hg]]
    'Route': ('route', 'to_str'),  # SDTM CM.CMROUTE
    'Route.1': ('route_1', 'to_str'),  # SDTM CM.CMROUTE
    'Route.10': ('route_10', 'to_str'),  # SDTM CM.CMROUTE
    'Route.11': ('route_11', 'to_str'),  # SDTM CM.CMROUTE
    'Route.12': ('route_12', 'to_str'),  # SDTM CM.CMROUTE
    'Route.13': ('route_13', 'to_str'),  # SDTM CM.CMROUTE
    'Route.14': ('route_14', 'to_str'),  # SDTM CM.CMROUTE
    'Route.2': ('route_2', 'to_str'),  # SDTM CM.CMROUTE
    'Route.3': ('route_3', 'to_str'),  # SDTM CM.CMROUTE
    'Route.4': ('route_4', 'to_str'),  # SDTM CM.CMROUTE
    'Route.5': ('route_5', 'to_str'),  # SDTM CM.CMROUTE
    'Route.6': ('route_6', 'to_str'),  # SDTM CM.CMROUTE
    'Route.7': ('route_7', 'to_str'),  # SDTM CM.CMROUTE
    'Route.8': ('route_8', 'to_str'),  # SDTM CM.CMROUTE
    'Route.9': ('route_9', 'to_str'),  # SDTM CM.CMROUTE
    'SWT': ('swt', 'to_float'),  # SDTM FA.IVSD | LOINC:18087-8 | [mm]
    'Serum triglycerides': ('serum_triglycerides', 'to_float'),  # SDTM LB.TRIG | LOINC:2571-8 | [mg/dL]
    'Shisha: How many minutes per session?': ('shisha_how_many_minutes_per_session', 'to_float'),  # SDTM SU.SUTRT
    'Shisha: How many sessions per day?': ('shisha_how_many_sessions_per_day', 'to_float'),  # SDTM SU.SUTRT
    'Sino-tubular junction (end diastole)': ('sino_tubular_junction_end_diastole', 'to_float'),  # SDTM FA.SINOTUB | [mm]
    'Sinus of Valsalva (end diastole)': ('sinus_of_valsalva_end_diastole', 'to_float'),  # SDTM FA.SINOVAL | [mm]
    'Smoking Index (Current)': ('smoking_index_current', 'to_float'),  # 
    'Smoking Index (Former)': ('smoking_index_former', 'to_float'),  # SDTM SU.PKYRFORM
    'Smoking years': ('smoking_years', 'to_float'),  # SDTM SU.ENDUR
    'Specify CT scan region(s) of interest': ('specify_ct_scan_region_s_of_interest', 'to_str'),  # SDTM SV.ADMIN
    'Specify MRI scan region(s) of interest': ('specify_mri_scan_region_s_of_interest', 'to_str'),  # SDTM SV.ADMIN
    'Specify X-Ray region(s) of interest': ('specify_x_ray_region_s_of_interest', 'to_str'),  # SDTM SV.ADMIN
    'Specify congenital defect': ('specify_congenital_defect', 'to_str'),  # SDTM SV.ADMIN
    'Specify degenerated valve(s) (choice=Aortic)': ('specify_degenerated_valve_s_choice_aortic', 'to_str'),  # SDTM SV.ADMIN
    'Specify degenerated valve(s) (choice=Mitral)': ('specify_degenerated_valve_s_choice_mitral', 'to_str'),  # SDTM SV.ADMIN
    'Specify degenerated valve(s) (choice=Pulmonary)': ('specify_degenerated_valve_s_choice_pulmonary', 'to_str'),  # SDTM SV.ADMIN
    'Specify degenerated valve(s) (choice=Tricuspid)': ('specify_degenerated_valve_s_choice_tricuspid', 'to_str'),  # SDTM SV.ADMIN
    'Specify other AHC clinic referral': ('specify_other_ahc_clinic_referral', 'to_str'),  # SDTM SV.ADMIN
    'Specify other lab work': ('specify_other_lab_work', 'to_str'),  # SDTM SV.ADMIN
    'Specify other requested imaging modality(ies)': ('specify_other_requested_imaging_modality_ies', 'to_str'),  # SDTM SV.ADMIN
    'Specify speciality clinic referral': ('specify_speciality_clinic_referral', 'to_str'),  # SDTM SV.ADMIN
    'Status': ('status', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.1': ('status_1', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.10': ('status_10', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.11': ('status_11', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.12': ('status_12', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.13': ('status_13', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.14': ('status_14', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.2': ('status_2', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.3': ('status_3', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.4': ('status_4', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.5': ('status_5', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.6': ('status_6', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.7': ('status_7', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.8': ('status_8', 'to_str'),  # SDTM CM.CMSTATUS
    'Status.9': ('status_9', 'to_str'),  # SDTM CM.CMSTATUS
    'Subject is on treatment?': ('subject_is_on_treatment', 'to_str'),  # SDTM SV.ADMIN
    'Systolic Blood Pressure - Right Brachial - Measurement 1': ('systolic_blood_pressure_right_brachial_measurement_1', 'to_float'),  # SDTM VS.SYSBP | LOINC:8480-6 | [mm[Hg]]
    'Systolic Blood Pressure - Right Brachial - Measurement 2': ('systolic_blood_pressure_right_brachial_measurement_2', 'to_float'),  # SDTM VS.SYSBP | LOINC:8480-6 | [mm[Hg]]
    'Systolic Blood Pressure - Right Brachial - Measurement 3': ('systolic_blood_pressure_right_brachial_measurement_3', 'to_float'),  # SDTM VS.SYSBP | LOINC:8480-6 | [mm[Hg]]
    'T3': ('t3', 'to_float'),  # SDTM LB.T3 | LOINC:3053-6 | [ng/dL]
    'T4': ('t4', 'to_float'),  # SDTM LB.T4 | LOINC:3026-2 | [ng/dL]
    'TAPSE': ('tapse', 'to_float'),  # SDTM FA.TAPSE | [mm]
    'TLC': ('tlc', 'to_float'),  # SDTM LB.WBC | LOINC:6690-2 | [10*3/uL]
    'TR': ('tr', 'to_str'),  # SDTM FA.TR
    'TS': ('ts', 'to_str'),  # SDTM FA.TS
    'TSH': ('tsh', 'to_float'),  # SDTM LB.TSH | LOINC:3016-3 | [uIU/mL]
    'Thyroid functions': ('thyroid_functions', 'to_bool'),  # SDTM SV.SVPRTRT
    'Time unit for smoking cessation duration': ('time_unit_for_smoking_cessation_duration', 'to_str'),  # SDTM SU.ADMIN
    'Total bilirubin': ('total_bilirubin', 'to_float'),  # SDTM LB.BILI | LOINC:1975-2 | [mg/dL]
    'Total cholesterol': ('total_cholesterol', 'to_float'),  # SDTM LB.CHOL | LOINC:2093-3 | [mg/dL]
    'Total daily dose': ('total_daily_dose', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.1': ('total_daily_dose_1', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.10': ('total_daily_dose_10', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.11': ('total_daily_dose_11', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.12': ('total_daily_dose_12', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.13': ('total_daily_dose_13', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.14': ('total_daily_dose_14', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.2': ('total_daily_dose_2', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.3': ('total_daily_dose_3', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.4': ('total_daily_dose_4', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.5': ('total_daily_dose_5', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.6': ('total_daily_dose_6', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.7': ('total_daily_dose_7', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.8': ('total_daily_dose_8', 'to_float'),  # SDTM CM.CMDOSE
    'Total daily dose.9': ('total_daily_dose_9', 'to_float'),  # SDTM CM.CMDOSE
    'Troponin': ('troponin', 'to_float'),  # SDTM LB.TRPI | LOINC:6598-7 | [ng/mL]
    'Tubular ascending aorta (end-diastole) distance from sinotubular junction': ('tubular_ascending_aorta_end_diastole_distance_from_sinotubular_', 'to_float'),  # SDTM FA.TUBAORTD | [mm]
    'Tubular ascending aorta (end-diastole) max diameter': ('tubular_ascending_aorta_end_diastole_max_diameter', 'to_float'),  # SDTM FA.TUBAORTD | [mm]
    'Upload consent scan 1': ('upload_consent_scan_1', 'to_str'),  # SDTM SV.ADMIN
    'Upload consent scan 2': ('upload_consent_scan_2', 'to_str'),  # SDTM SV.ADMIN
    'Upper limb Duplex': ('upper_limb_duplex', 'to_bool'),  # SDTM SV.SVPRTRT
    'Urea': ('urea', 'to_float'),  # SDTM LB.UREA | LOINC:3091-6 | [mg/dL]
    'Valvular Heart Disease (choice=(1) Congenital)': ('valvular_heart_disease_choice_1_congenital', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(2) Rheumatic)': ('valvular_heart_disease_choice_2_rheumatic', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(3) Degenerative)': ('valvular_heart_disease_choice_3_degenerative', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(4) Mitral valve diseases)': ('valvular_heart_disease_choice_4_mitral_valve_diseases', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(4.0) Mitral stenosis)': ('valvular_heart_disease_choice_4_0_mitral_stenosis', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(4.1) mitral insufficiency)': ('valvular_heart_disease_choice_4_1_mitral_insufficiency', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(4.2) Mitral stenosis with insufficiency)': ('valvular_heart_disease_choice_4_2_mitral_stenosis_with_insuffic', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(4.3) Mitral (valve) prolapse)': ('valvular_heart_disease_choice_4_3_mitral_valve_prolapse', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(5) Aortic valve diseases)': ('valvular_heart_disease_choice_5_aortic_valve_diseases', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(5.0) Aortic stenosis)': ('valvular_heart_disease_choice_5_0_aortic_stenosis', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(5.1) Aortic insufficiency)': ('valvular_heart_disease_choice_5_1_aortic_insufficiency', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(5.2) Aortic stenosis with insufficiency)': ('valvular_heart_disease_choice_5_2_aortic_stenosis_with_insuffic', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(5.3) Bicuspid aortic valve)': ('valvular_heart_disease_choice_5_3_bicuspid_aortic_valve', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(6) Tricuspid valve diseases)': ('valvular_heart_disease_choice_6_tricuspid_valve_diseases', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(6.0) Tricuspid stenosis)': ('valvular_heart_disease_choice_6_0_tricuspid_stenosis', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(6.1) Tricuspid insufficiency)': ('valvular_heart_disease_choice_6_1_tricuspid_insufficiency', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(6.2) Tricuspid stenosis with insufficiency)': ('valvular_heart_disease_choice_6_2_tricuspid_stenosis_with_insuf', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(7) Pulmonary valve diseases)': ('valvular_heart_disease_choice_7_pulmonary_valve_diseases', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(7.0) Pulmonary stenosis)': ('valvular_heart_disease_choice_7_0_pulmonary_stenosis', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(7.1) Pulmonary insufficiency)': ('valvular_heart_disease_choice_7_1_pulmonary_insufficiency', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(7.2) Pulmonary stenosis with insufficiency)': ('valvular_heart_disease_choice_7_2_pulmonary_stenosis_with_insuf', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(8) Multiple valve diseases)': ('valvular_heart_disease_choice_8_multiple_valve_diseases', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(8.0) Disorders of both mitral and aortic valves)': ('valvular_heart_disease_choice_8_0_disorders_of_both_mitral_and_', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(8.1) Disorders of both mitral and tricuspid valves)': ('valvular_heart_disease_choice_8_1_disorders_of_both_mitral_and_', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(8.2) Disorders of both aortic and tricuspid valves)': ('valvular_heart_disease_choice_8_2_disorders_of_both_aortic_and_', 'to_bool'),  # SDTM FA.MHTERM
    'Valvular Heart Disease (choice=(8.3) Combined disorders of mitral, aortic and tricuspid valves)': ('valvular_heart_disease_choice_8_3_combined_disorders_of_mitral_', 'to_bool'),  # SDTM FA.MHTERM
    'Ventricular Rate': ('ventricular_rate', 'to_float'),  # SDTM EG.HR | LOINC:8867-4 | [/min]
    'Waist : Hip Ratio': ('waist_hip_ratio', 'to_float'),  # SDTM VS.WHR | LOINC:73708-0 | [1]
    'Waist circumference in cm': ('waist_circumference_in_cm', 'to_float'),  # SDTM VS.WAISTCIR | LOINC:56115-9 | [cm]
    'Weight in kg': ('weight_in_kg', 'to_float'),  # SDTM VS.WEIGHT | LOINC:29463-7 | [kg]
    'What ethnicity do you consider yourself?': ('what_ethnicity_do_you_consider_yourself', 'to_str'),  # SDTM DM.COUNTRY
    'What is the familial relationship between you and your spouse?': ('what_is_the_familial_relationship_between_you_and_your_spouse', 'to_str'),  # SDTM DM.MARSTATS
    'What is the familial relationship between your father and mother?': ('what_is_the_familial_relationship_between_your_father_and_mothe', 'to_str'),  # 
    'What is your current smoking status?': ('what_is_your_current_smoking_status', 'to_str'),  # 
    'What is your marital status?': ('what_is_your_marital_status', 'to_str'),  # SDTM DM.MARSTATS
    'What is your occupational status?': ('what_is_your_occupational_status', 'to_str'),  # SDTM SC.SCTEST
    'When you get any pain or discomfort in your chest what do you do?': ('when_you_get_any_pain_or_discomfort_in_your_chest_what_do_you_d', 'to_str'),  # SDTM MH.MHTERM
    'Where': ('where', 'to_str'),  # SDTM SV.ADMIN
    'Why there are missing data that cannot be acquired in this sheet?': ('why_there_are_missing_data_that_cannot_be_acquired_in_this_shee', 'to_str'),  # SDTM SV.ADMIN
    'X-Ray - Specify': ('x_ray_specify', 'to_str'),  # SDTM SV.ADMIN
    'and specify age of onset': ('and_specify_age_of_onset', 'to_str'),  # SDTM SV.ADMIN
    'corrected QT interval': ('corrected_qt_interval', 'to_float'),  # SDTM EG.QTC | LOINC:8636-3 | [ms]
    'eGFR (Female)': ('egfr_female', 'to_float'),  # SDTM LB.EGFR | LOINC:70969-1 | [mL/min/1.73m2]
    'eGFR (Male)': ('egfr_male', 'to_float'),  # SDTM LB.EGFR | LOINC:70969-1 | [mL/min/1.73m2]
    'if more than 1 wife, how many?': ('if_more_than_1_wife_how_many', 'to_str'),  # SDTM SV.ADMIN
    'vLDL': ('vldl', 'to_float'),  # SDTM LB.VLDL | LOINC:13458-5 | [mg/dL]
}
