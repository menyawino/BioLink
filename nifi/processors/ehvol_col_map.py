    # Auto-generated — EHVol column map for NiFi BiolinkSchemaStandardizerProcessor
# Source: standardized schema build output  →  standardized_columns.csv
# Format: {original_col_name: (pg_col_name, coerce_func_name)}
# DO NOT EDIT by hand; re-run the schema build step instead.
COLUMN_MAP = {
    'Consent Scan': ('consent_scan', 'to_str'),  # SDTM SV.ADMIN
    'Consent obtained?': ('consent_obtained', 'to_str'),  # SDTM SV.ADMIN
    'Abnormal physical structure': ('abnormal_physical_structure', 'to_bool'),  # SDTM SC.SCPHYDEF
    'Address': ('address', 'to_str'),  # SDTM DM.SITEID
    'Age': ('age', 'to_int'),  # SDTM DM.AGE | LOINC:30525-0 | [a]
    'Amount of Alcohol': ('amount_of_alcohol', 'to_str'),  # SDTM SV.ADMIN
    'Anaemia': ('anaemia', 'to_bool'),  # SDTM MH.MHTERM
    'Aortic Regurge': ('aortic_regurge', 'to_str'),  # SDTM FA.AR
    'Aortic Root': ('aortic_root', 'to_float'),  # SDTM FA.AORTROOT | LOINC:18028-2 | [mm]
    'Aortic Stenosis': ('aortic_stenosis', 'to_str'),  # SDTM FA.AS
    'Are you one of a twin or triplet ?': ('are_you_one_of_a_twin_or_triplet', 'to_bool'),  # SDTM DM.TWIN
    'Are your parents, grandparents or great grandparents from non-Egyptian origin?': ('are_your_parents_grandparents_or_great_grandparents_from_non_eg', 'to_bool'),  # SDTM IE.IESPCAT
    'Autoimmune problems': ('autoimmune_problems', 'to_bool'),  # SDTM MH.MHTERM
    'BMI': ('bmi', 'to_float'),  # SDTM VS.BMI | LOINC:39156-5 | [kg/m2]
    'BP': ('bp', 'to_float'),  # SDTM VS.DIABP | LOINC:8462-4 | [mm[Hg]]
    'BSA': ('bsa', 'to_float'),  # SDTM VS.BSA | LOINC:3140-1 | [m2]
    'City of Residence during childhood': ('city_of_residence_during_childhood', 'to_str'),  # SDTM DM.CHLDCITY
    'Communication difficulties': ('communication_difficulties', 'to_bool'),  # SDTM IE.IESPCAT
    'Complete?': ('complete', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.1': ('complete_1', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.2': ('complete_2', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.3': ('complete_3', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.4': ('complete_4', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.5': ('complete_5', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.6': ('complete_6', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.7': ('complete_7', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.8': ('complete_8', 'to_bool'),  # SDTM SV.SVCOMP
    'Complete?.9': ('complete_9', 'to_bool'),  # SDTM SV.SVCOMP
    'Consanguinous Marriage': ('consanguinous_marriage', 'to_bool'),  # SDTM DM.CONSANG
    'Contraindications for MRI': ('contraindications_for_mri', 'to_bool'),  # SDTM IE.IESPCAT
    'Current City of Residence': ('current_city_of_residence', 'to_str'),  # SDTM DM.SITEID
    'Current/Recent Smoker (< 1 year)': ('current_recent_smoker_1_year', 'to_str'),  # 
    'DNA ID': ('dna_id', 'to_str'),  # SDTM DM.USUBJID
    'Date of Birth': ('date_of_birth', 'to_date'),  # SDTM DM.BRTHDTC | LOINC:21112-8
    'Date of Enrolment': ('date_of_enrolment', 'to_date'),  # SDTM DM.RFICDTC
    'Diabetes Mellitus': ('diabetes_mellitus', 'to_str'),  # 
    'Diabetes Therapy': ('diabetes_therapy', 'to_str'),  # SDTM CM.CMCAT
    'Do any of your own children, parents or siblings have any of the following health conditions (choice=Diabetes)': ('do_any_of_your_own_children_parents_or_siblings_have_any_of_the', 'to_bool'),  # 
    'Do any of your own children, parents or siblings have any of the following health conditions (choice=Heart Disease)': ('do_any_of_your_own_children_parents_or_siblings_have_any_of_t_2', 'to_bool'),  # 
    'Do any of your own children, parents or siblings have any of the following health conditions (choice=High Blood Pressure)': ('do_any_of_your_own_children_parents_or_siblings_have_any_of_t_3', 'to_bool'),  # 
    'Do any of your own children, parents or siblings have any of the following health conditions (choice=Stroke)': ('do_any_of_your_own_children_parents_or_siblings_have_any_of_t_4', 'to_bool'),  # 
    'Do any of your own children, parents or siblings have any of the following health conditions (choice=Sudden unexpected death)': ('do_any_of_your_own_children_parents_or_siblings_have_any_of_t_5', 'to_bool'),  # 
    'Do you drink alcohol?': ('do_you_drink_alcohol', 'to_bool'),  # SDTM MH.MHTERM
    'Do you take any medication currently?': ('do_you_take_any_medication_currently', 'to_bool'),  # SDTM MH.MHTERM
    'Do you wish to be informed if we discover any abnormality was detected during the course of this study?': ('do_you_wish_to_be_informed_if_we_discover_any_abnormality_was_d', 'to_bool'),  # SDTM MH.MHTERM
    'Does any other non-cardiac condition run in your family?': ('does_any_other_non_cardiac_condition_run_in_your_family', 'to_str'),  # SDTM SV.ADMIN
    'Dyslipidemia': ('dyslipidemia', 'to_str'),  # 
    'ECG_Conclusion': ('ecg_conclusion', 'to_str'),  # SDTM EG.EGSTRESC
    'EF': ('ef', 'to_float'),  # SDTM FA.EF | LOINC:18052-2 | [%]
    'Echo Date': ('echo_date', 'to_date'),  # SDTM FA.FADTC
    'Email': ('email', 'to_str'),  # SDTM SV.ADMIN
    'Examination Date': ('examination_date', 'to_date'),  # SDTM SV.SVSTDTC
    'FS': ('fs', 'to_float'),  # SDTM FA.LVFS | LOINC:18049-8 | [%]
    'Fat Mass': ('fat_mass', 'to_float'),  # SDTM VS.FATMASS | LOINC:73708-0 | [kg]
    'Fat-Free Mass': ('fat_free_mass', 'to_float'),  # SDTM VS.LEANMASS | [kg]
    "Father's City of Origin": ('father_s_city_of_origin', 'to_str'),  # 
    "Father's City of Origin.1": ('father_s_city_of_origin_1', 'to_str'),  # 
    'From where?': ('from_where', 'to_str'),  # SDTM SV.ADMIN
    'Gender': ('gender', 'to_str'),  # SDTM DM.SEX | LOINC:46098-0
    'Have you undergone an operation or any surgical procedures?': ('have_you_undergone_an_operation_or_any_surgical_procedures', 'to_bool'),  # SDTM MH.MHTERM
    'HbA1c': ('hba1c', 'to_float'),  # SDTM LB.HBA1C | LOINC:4548-4 | [%]
    'Heart Attack or Angina': ('heart_attack_or_angina', 'to_bool'),  # SDTM MH.MHTERM
    'Heart Rate': ('heart_rate', 'to_float'),  # SDTM VS.HR | LOINC:8867-4 | [/min]
    'Heart Rate during MRI': ('heart_rate_during_mri', 'to_float'),  # SDTM VS.HR | LOINC:8867-4 | [/min]
    'Height (cm)': ('height_cm', 'to_float'),  # SDTM VS.HEIGHT | LOINC:8302-2 | [cm]
    'High blood pressure': ('high_blood_pressure', 'to_str'),  # 
    'History of Familial Cardiomyopathies': ('history_of_familial_cardiomyopathies', 'to_bool'),  # 
    'History of Premature CAD': ('history_of_premature_cad', 'to_bool'),  # 
    'History of Sudden Death History': ('history_of_sudden_death_history', 'to_bool'),  # SDTM MH.MHTERM
    'Home Tel.': ('home_tel', 'to_str'),  # SDTM SV.ADMIN
    'Home Tel. 2': ('home_tel_2', 'to_str'),  # SDTM SV.ADMIN
    'How long have you been smoking?': ('how_long_have_you_been_smoking', 'to_float'),  # SDTM SU.ENDUR
    'How many cigarettes have you been smoking a day before you quit?': ('how_many_cigarettes_have_you_been_smoking_a_day_before_you_quit', 'to_int'),  # SDTM SU.SUCAT
    'How many cigarettes have you been smoking a day?': ('how_many_cigarettes_have_you_been_smoking_a_day', 'to_int'),  # SDTM SU.SUCAT
    'How many siblings you have?': ('how_many_siblings_you_have', 'to_int'),  # SDTM DM.NSIBLING
    'How many years have you been smoking?': ('how_many_years_have_you_been_smoking', 'to_float'),  # SDTM SU.ENDUR
    'IVSd': ('ivsd', 'to_float'),  # SDTM FA.IVSD | LOINC:18087-8 | [mm]
    'IVSs': ('ivss', 'to_float'),  # SDTM FA.IVSSYS | LOINC:29430-6 | [mm]
    'Is there any chance you might be pregnant?': ('is_there_any_chance_you_might_be_pregnant', 'to_bool'),  # SDTM IE.IESPCAT
    'JVP': ('jvp', 'to_str'),  # SDTM VS.JVP
    'Kidney problems': ('kidney_problems', 'to_bool'),  # SDTM MH.MHTERM
    'Known CVS disease': ('known_cvs_disease', 'to_bool'),  # SDTM IE.IESPCAT
    'Known Collagen disease': ('known_collagen_disease', 'to_bool'),  # SDTM IE.IESPCAT
    'LVEDD': ('lvedd', 'to_float'),  # SDTM FA.LVEDD | LOINC:18026-6 | [mm]
    'LVESD': ('lvesd', 'to_float'),  # SDTM FA.LVESD | LOINC:18150-4 | [mm]
    'LVM': ('lvm', 'to_float'),  # SDTM FA.LVM | LOINC:18086-0 | [g]
    'LVPWd': ('lvpwd', 'to_float'),  # LOINC:29430-6 | [mm]
    'LVPWs': ('lvpws', 'to_float'),  # SDTM FA.LVPWSYST | LOINC:29430-6 | [mm]
    'Left Atrium': ('left_atrium', 'to_float'),  # SDTM FA.LADIAM | LOINC:18035-7 | [mm]
    'Left ventricular EF': ('left_ventricular_ef', 'to_float'),  # SDTM FA.EF | LOINC:18052-2 | [%]
    'Left ventricular ejection fraction': ('left_ventricular_ejection_fraction', 'to_float'),  # SDTM FA.LVEF | LOINC:18052-2 | [%]
    'Left ventricular end diastolic volume': ('left_ventricular_end_diastolic_volume', 'to_float'),  # SDTM FA.LVEDV | LOINC:18026-6 | [mL]
    'Left ventricular end systolic volume': ('left_ventricular_end_systolic_volume', 'to_float'),  # SDTM FA.LVESV | LOINC:18150-4 | [mL]
    'Left ventricular mass': ('left_ventricular_mass', 'to_float'),  # SDTM FA.LVM | LOINC:18086-0 | [g]
    'List these medications': ('list_these_medications', 'to_str'),  # SDTM SV.ADMIN
    'Liver Problems': ('liver_problems', 'to_bool'),  # SDTM MH.MHTERM
    'Lung Problems': ('lung_problems', 'to_bool'),  # SDTM MH.MHTERM
    'MRI': ('mri', 'to_str'),  # SDTM FA.MRI
    'MRI Date': ('mri_date', 'to_date'),  # SDTM FA.MRIDTC
    'Malignancy': ('malignancy', 'to_bool'),  # SDTM MH.MHTERM
    'Malignancy details': ('malignancy_details', 'to_str'),  # SDTM SV.ADMIN
    'Marital Status': ('marital_status', 'to_str'),  # SDTM DM.MARSTATS
    'Mitral Regurge': ('mitral_regurge', 'to_str'),  # SDTM FA.MR
    'Mitral Stenosis': ('mitral_stenosis', 'to_str'),  # SDTM FA.MS
    'Mobile Tel.': ('mobile_tel', 'to_str'),  # SDTM SV.ADMIN
    'Mobile Tel. 2': ('mobile_tel_2', 'to_str'),  # SDTM SV.ADMIN
    'Muscloskeletal Problems': ('muscloskeletal_problems', 'to_bool'),  # SDTM MH.MHTERM
    'Name': ('name', 'to_str'),  # SDTM CM.CMTRT
    'Name.1': ('name_1', 'to_str'),  # SDTM CM.CMTRT
    'Nationality': ('nationality', 'to_str'),  # SDTM DM.COUNTRY
    'Neurological problems': ('neurological_problems', 'to_bool'),  # SDTM MH.MHTERM
    'Non-Egyptian Parents?': ('non_egyptian_parents', 'to_bool'),  # SDTM IE.IESPCAT
    'Notes': ('notes', 'to_str'),  # SDTM SV.ADMIN
    'Number of Children': ('number_of_children', 'to_int'),  # SDTM DM.NCHILD
    'Number of wives': ('number_of_wives', 'to_int'),  # SDTM DM.NWIVES
    'Offspring of Consanguinous Marriage': ('offspring_of_consanguinous_marriage', 'to_str'),  # 
    'Other': ('other', 'to_str'),  # SDTM SV.ADMIN
    'Other Findings': ('other_findings', 'to_str'),  # SDTM SV.ADMIN
    'Other MRI findings': ('other_mri_findings', 'to_str'),  # SDTM FA.FAOTHER
    'P wave abnormality': ('p_wave_abnormality', 'to_str'),  # SDTM EG.EGPWAVE | LOINC:8625-3
    'PR interval': ('pr_interval', 'to_float'),  # SDTM EG.PR | LOINC:8625-6 | [ms]
    "Parents' occupation": ('parents_occupation', 'to_str'),  # SDTM SC.SCTEST
    'Physical abnormality details': ('physical_abnormality_details', 'to_str'),  # SDTM SV.ADMIN
    'Pregnant female': ('pregnant_female', 'to_bool'),  # SDTM IE.IESPCAT
    'Prior Heart Failure (previous Hx)': ('prior_heart_failure_previous_hx', 'to_str'),  # 
    'Procedure details': ('procedure_details', 'to_str'),  # SDTM SV.ADMIN
    'Pulmonary Regurge': ('pulmonary_regurge', 'to_str'),  # 
    'Pulmonary stenosis': ('pulmonary_stenosis', 'to_str'),  # SDTM FA.PS
    'QRS abnormalities': ('qrs_abnormalities', 'to_str'),  # SDTM EG.EGQRS | LOINC:8633-7
    'QRS duration': ('qrs_duration', 'to_float'),  # SDTM EG.QRSDUR | LOINC:8625-6 | [ms]
    'QTc interval': ('qtc_interval', 'to_float'),  # SDTM EG.QTC | LOINC:8636-3 | [ms]
    'Rate': ('rate', 'to_float'),  # SDTM EG.EGRATE | LOINC:8867-4 | [/min]
    'Record ID': ('record_id', 'to_str'),  # 
    'Regularity': ('regularity', 'to_str'),  # SDTM EG.EGREG
    'Rheumatic Fever': ('rheumatic_fever', 'to_bool'),  # SDTM MH.MHTERM
    'Rhythm': ('rhythm', 'to_str'),  # SDTM EG.RHYTHM
    'Right Ventricle': ('right_ventricle', 'to_float'),  # SDTM FA.RVDIAM | LOINC:18015-9 | [mm]
    'Right ventricular EF': ('right_ventricular_ef', 'to_float'),  # SDTM FA.RVEF | LOINC:10230-1 | [%]
    'S1': ('s1', 'to_str'),  # SDTM FA.FACLIN
    'S2': ('s2', 'to_str'),  # SDTM FA.FACLIN
    'S3': ('s3', 'to_bool'),  # SDTM FA.S3SOUND | LOINC:48451-8
    'S4': ('s4', 'to_bool'),  # SDTM FA.S4SOUND | LOINC:48452-6
    'ST segment abnormalities': ('st_segment_abnormalities', 'to_str'),  # SDTM EG.EGSTWAVE | LOINC:8625-3
    'Span (cm)': ('span_cm', 'to_float'),  # SDTM VS.ARMSPAN | [cm]
    'Specifiy P wave abnormality': ('specifiy_p_wave_abnormality', 'to_str'),  # SDTM SV.ADMIN
    'Specifiy QRS abnormality': ('specifiy_qrs_abnormality', 'to_str'),  # SDTM SV.ADMIN
    'Specifiy ST seg. abnormality': ('specifiy_st_seg_abnormality', 'to_str'),  # SDTM SV.ADMIN
    'Specifiy T wave abnormality': ('specifiy_t_wave_abnormality', 'to_str'),  # SDTM SV.ADMIN
    'Subaortic Membrane': ('subaortic_membrane', 'to_bool'),  # SDTM FA.SUBAORT
    'T wave abnormalities': ('t_wave_abnormalities', 'to_str'),  # SDTM EG.EGTWAVE | LOINC:8625-3
    'Tricuspid Regurge': ('tricuspid_regurge', 'to_str'),  # SDTM FA.TR
    'Tricuspid Stenosis': ('tricuspid_stenosis', 'to_str'),  # SDTM FA.TS
    'Troponin I': ('troponin_i', 'to_float'),  # SDTM LB.TRPI | LOINC:42757-5 | [ng/mL]
    'Type': ('type', 'to_str'),  # SDTM SV.ADMIN
    'Unwilling to participate': ('unwilling_to_participate', 'to_bool'),  # SDTM IE.IESPCAT
    'Volunteer under 18 year old ?': ('volunteer_under_18_year_old', 'to_bool'),  # SDTM IE.IESPCAT
    'We may contact you yearly to follow up on your health, do you accept?': ('we_may_contact_you_yearly_to_follow_up_on_your_health_do_you_ac', 'to_str'),  # SDTM SV.ADMIN
    'Weight (kg)': ('weight_kg', 'to_float'),  # SDTM VS.WEIGHT | LOINC:29463-7 | [kg]
    'What is this(these) condition(s)?': ('what_is_this_these_condition_s', 'to_str'),  # SDTM SV.ADMIN
    'Where did you spend your childhood?': ('where_did_you_spend_your_childhood', 'to_str'),  # SDTM SV.ADMIN
    'Who and what disease?': ('who_and_what_disease', 'to_str'),  # SDTM SV.ADMIN
}
