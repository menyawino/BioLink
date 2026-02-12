/*
    Staging model: clean, cast, and rename raw EHVol columns.
    Source: public.ehvol_raw
    Target: public.stg_ehvol
*/

with source as (
    select * from {{ source('raw', 'ehvol_raw') }}
),

renamed as (

    select
        -- Identifiers
        record_id::int                                          as record_id,
        name                                                    as name_arabic,
        name_1                                                  as name_english,
        dna_id                                                  as dna_id,

        -- Demographics
        case when date_of_birth ~ '^\d{1,2}/\d{1,2}/\d{4}$'
             then to_date(date_of_birth, 'MM/DD/YYYY')
             else date_of_birth::date end                       as dob,
        age::int                                                as age,
        gender                                                  as gender,
        nationality                                             as nationality,
        father_s_city_of_origin                                 as father_city,
        city_of_residence_during_childhood                      as childhood_city,
        current_city_of_residence                               as current_city,
        marital_status                                          as marital_status,
        parents_occupation                                      as parents_occupation,
        
        -- Contact
        home_tel                                                as phone_home_1,
        home_tel_2                                              as phone_home_2,
        mobile_tel                                              as phone_mobile_1,
        mobile_tel_2                                            as phone_mobile_2,
        email                                                   as email,
        address                                                 as address,

        -- Study Admin
        case when date_of_enrolment ~ '^\d{1,2}/\d{1,2}/\d{4}$'
             then to_date(date_of_enrolment, 'MM/DD/YYYY')
             else date_of_enrolment::date end                   as enrollment_date,
        consent_obtained                                        as consent_obtained,
        
        -- Physical / Habits
        current_recent_smoker_1_year                            as smoker_current,
        how_long_have_you_been_smoking                          as smoker_duration,
        how_many_cigarettes_have_you_been_smoking_a_day         as smoker_cigs_per_day,
        how_many_years_have_you_been_smoking                    as smoker_years,
        how_many_cigarettes_have_you_been_smoking_a_day_before_you_quit as quit_cigs_per_day,
        do_you_drink_alcohol                                    as alcohol_use,
        amount_of_alcohol                                       as alcohol_amount,

        -- Medical History & Exclusion
        is_there_any_chance_you_might_be_pregnant               as pregnancy_chance,
        volunteer_under_18_year_old                             as exclude_under_18,
        non_egyptian_parents                                    as exclude_non_egyptian,
        pregnant_female                                         as exclude_pregnant,
        unwilling_to_participate                                as exclude_unwilling,
        
        known_cvs_disease                                       as history_cvs,
        known_collagen_disease                                  as history_collagen,
        history_of_sudden_death_history                         as history_sudden_death,
        history_of_familial_cardiomyopathies                    as history_familial_cm,
        history_of_premature_cad                                as history_premature_cad,
        prior_heart_failure_previous_hx                         as history_heart_failure,
        have_you_undergone_an_operation_or_any_surgical_procedures as history_surgery,
        procedure_details                                       as surgery_details,
        malignancy                                              as history_malignancy,
        malignancy_details                                      as malignancy_details,

        -- Comorbidities
        case when lower(heart_attack_or_angina) in ('yes','true','1') then true else false end as comorb_mi_angina,
        case when lower(high_blood_pressure) in ('yes','true','1') then true else false end as comorb_htn,
        case when lower(dyslipidemia) in ('yes','true','1') then true else false end as comorb_dyslipidemia,
        case when lower(rheumatic_fever) in ('yes','true','1') then true else false end as comorb_rheumatic,
        case when lower(anaemia) in ('yes','true','1') then true else false end as comorb_anemia,
        case when lower(lung_problems) in ('yes','true','1') then true else false end as comorb_lung,
        case when lower(kidney_problems) in ('yes','true','1') then true else false end as comorb_kidney,
        case when lower(liver_problems) in ('yes','true','1') then true else false end as comorb_liver,
        case when lower(diabetes_mellitus) in ('yes','true','1') then true else false end as comorb_dm,
        diabetes_therapy                                        as dm_therapy,
        case when lower(neurological_problems) in ('yes','true','1') then true else false end as comorb_neuro,
        case when lower(muscloskeletal_problems) in ('yes','true','1') then true else false end as comorb_msk,
        case when lower(autoimmune_problems) in ('yes','true','1') then true else false end as comorb_autoimmune,
        
        do_you_take_any_medication_currently                    as meds_current,
        list_these_medications                                  as meds_list,

        -- Family History
        offspring_of_consanguinous_marriage                     as parents_consanguineous,
        consanguinous_marriage                                  as own_consanguineous,
        number_of_children                                      as children_count,
        how_many_siblings_you_have                              as siblings_count,
        are_you_one_of_a_twin_or_triplet                        as is_multiple_birth,
        
        -- Family Conditions (mapped from truncated dlt names)
        do_any_of_your_own_children_pmijayaditions_choice_heart_disease as fam_hist_heart,
        do_any_of_your_own_children_pd9hk9qlth_conditions_choice_stroke as fam_hist_stroke,
        do_any_of_your_own_children_pugzceqh_conditions_choice_diabetes as fam_hist_dm,
        do_any_of_your_own_children_phwca8as_choice_high_blood_pressure as fam_hist_htn,
        do_any_of_your_own_children_pmyqbqwoice_sudden_unexpected_death as fam_hist_sds,
        does_any_other_non_cardiac_condition_run_in_your_family         as fam_hist_other,
        what_is_this_these_condition_s                          as fam_hist_other_details,
        
        -- Exam & Vitals
        case when examination_date ~ '^\d{1,2}/\d{1,2}/\d{4}$'
             then to_date(examination_date, 'MM/DD/YYYY')
             else examination_date::date end                    as exam_date,
        nullif(heart_rate, '')::numeric                         as hr,
        regularity                                              as hr_regularity,
        bp                                                      as bp_combined,
        nullif(height_cm, '')::numeric                          as height_cm,
        nullif(weight_kg, '')::numeric                          as weight_kg,
        nullif(bmi, '')::numeric                                as bmi,
        nullif(bsa, '')::numeric                                as bsa,
        jvp                                                     as jvp,
        abnormal_physical_structure                             as phys_abnormal,
        physical_abnormality_details                            as phys_abnormal_details,
        s1, s2, s3, s4,                                         -- Keep as is
        other_findings                                          as exam_other,
        
        -- Labs
        nullif(hba1c, '')::numeric                              as hba1c,
        nullif(troponin_i, '')::numeric                         as troponin_i,

        -- ECG
        nullif(rate, '')::numeric                               as ecg_rate,
        rhythm                                                  as ecg_rhythm,
        p_wave_abnormality                                      as ecg_p_abnormal,
        specifiy_p_wave_abnormality                             as ecg_p_detail,
        nullif(pr_interval, '')::numeric                        as ecg_pr,
        qrs_duration                                            as ecg_qrs_dur,
        qrs_abnormalities                                       as ecg_qrs_abnormal,
        specifiy_qrs_abnormality                                as ecg_qrs_detail,
        st_segment_abnormalities                                as ecg_st_abnormal,
        specifiy_st_seg_abnormality                             as ecg_st_detail,
        nullif(qtc_interval, '')::numeric                       as ecg_qtc,
        t_wave_abnormalities                                    as ecg_t_abnormal,
        specifiy_t_wave_abnormality                             as ecg_t_detail,
        ecg_conclusion                                          as ecg_conclusion,

        -- Echo
        case when echo_date ~ '^\d{1,2}/\d{1,2}/\d{4}$'
             then to_date(echo_date, 'MM/DD/YYYY')
             else echo_date::date end                           as echo_date,
        aortic_root                                             as echo_aortic_root,
        left_atrium                                             as echo_la,
        right_ventricle                                         as echo_rv,
        nullif(lvedd, '')::numeric                              as echo_lvedd,
        nullif(lvesd, '')::numeric                              as echo_lvesd,
        nullif(ivsd, '')::numeric                               as echo_ivsd,
        nullif(ivss, '')::numeric                               as echo_ivss,
        nullif(lvpwd, '')::numeric                              as echo_lvpwd,
        nullif(lvpws, '')::numeric                              as echo_lvpws,
        lvm                                                     as echo_lvm,
        nullif(regexp_replace(ef, '[^0-9.]', '', 'g'), '')::numeric as echo_ef,
        nullif(regexp_replace(fs, '[^0-9.]', '', 'g'), '')::numeric as echo_fs,
        
        -- Echo valvular
        mitral_regurge                                          as echo_mr,
        mitral_stenosis                                         as echo_ms,
        tricuspid_regurge                                       as echo_tr,
        tricuspid_stenosis                                      as echo_ts,
        aortic_regurge                                          as echo_ar,
        aortic_stenosis                                         as echo_as,
        pulmonary_regurge                                       as echo_pr,
        pulmonary_stenosis                                      as echo_ps,
        
        -- MRI
        mri                                                     as has_mri,
        case when mri_date ~ '^\d{1,2}/\d{1,2}/\d{4}$'
             then to_date(mri_date, 'MM/DD/YYYY')
             else mri_date::date end                            as mri_date,
        nullif(regexp_replace(left_ventricular_ejection_fraction, '[^0-9.]', '', 'g'), '')::numeric as mri_lvef,
        nullif(regexp_replace(left_ventricular_end_diastolic_volume, '[^0-9.]', '', 'g'), '')::numeric as mri_lvedv,
        nullif(regexp_replace(left_ventricular_end_systolic_volume, '[^0-9.]', '', 'g'), '')::numeric as mri_lvesv,
        nullif(regexp_replace(left_ventricular_mass, '[^0-9.]', '', 'g'), '')::numeric as mri_lv_mass,
        nullif(regexp_replace(left_ventricular_ef, '[^0-9.]', '', 'g'), '')::numeric as mri_lvef_2,
        nullif(regexp_replace(right_ventricular_ef, '[^0-9.]', '', 'g'), '')::numeric as mri_rvef,
        other_mri_findings                                      as mri_other,
        
        notes                                                   as notes

    from source
),

final as (
    select
        *,
        -- Derived: ISO 3166-2 for current city
        case
            when current_city is null or trim(current_city) = '' then null
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('cairo', 'al qahirah', 'القاهرة') then 'EG-C'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('alexandria', 'al iskanadariyah', 'الإسكندرية', 'الاسكندرية') then 'EG-ALX'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('giza', 'al jizah', 'الجيزة') then 'EG-GZ'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('aswan', 'أسوان', 'اسوان') then 'EG-ASN'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('asyut', 'أسيوط', 'اسيوط') then 'EG-AST'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('beheira', 'al buhayrah', 'البحيرة') then 'EG-BH'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('beni suef', 'beni-suef', 'بني سويف') then 'EG-BNS'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('dakahlia', 'ad dakhiliyah', 'الدقهلية') then 'EG-DK'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('damietta', 'دمياط') then 'EG-DT'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('faiyum', 'al fayyum', 'الفيوم') then 'EG-FYM'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('gharbia', 'al gharbiyah', 'الغربية') then 'EG-GH'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('ismailia', 'al ismailiyah', 'الإسماعيلية', 'الاسماعيلية') then 'EG-IS'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('kafr el sheikh', 'kafr el-sheikh', 'كفر الشيخ') then 'EG-KFS'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('luxor', 'الأقصر', 'الاقصر') then 'EG-LX'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('matrouh', 'marsa matruh', 'مطروح', 'مرسى مطروح') then 'EG-MT'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('minya', 'المنيا') then 'EG-MN'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('monufia', 'al minufiyah', 'المنوفية') then 'EG-MNF'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('new valley', 'al wadi al jadid', 'الوادي الجديد') then 'EG-WAD'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('north sinai', 'shamal sina', 'شمال سيناء') then 'EG-SIN'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('port said', 'بورسعيد', 'بور سعيد') then 'EG-PTS'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('qalyubia', 'القليوبية') then 'EG-KB'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('qena', 'قنا') then 'EG-KN'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('red sea', 'al bahr al ahmar', 'البحر الأحمر', 'البحر الاحمر') then 'EG-BA'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('sharqia', 'ash sharqiyah', 'الشرقية') then 'EG-SHR'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('sohag', 'سوهاج') then 'EG-SHG'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('south sinai', 'janub sina', 'جنوب سيناء') then 'EG-JS'
            when lower(regexp_replace(trim(current_city), '\s+', ' ', 'g')) in ('suez', 'السويس') then 'EG-SUZ'
            else null
        end as current_city_iso_3166_2,

        -- Derived: BP components
        case when bp_combined is not null and bp_combined ~ '^\d+\.\d+$'
             then split_part(bp_combined, '.', 1)::numeric end  as systolic_bp,
        case when bp_combined is not null and bp_combined ~ '^\d+\.\d+$'
             then split_part(bp_combined, '.', 2)::numeric end  as diastolic_bp,
             
        -- Derived: Ever smoked
        case when lower(smoker_current) in ('yes','true','1') 
               or coalesce(smoker_years, '0')::int > 0 
             then true else false end                           as ever_smoked
             
    from renamed
)

select * from final
