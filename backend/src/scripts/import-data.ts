import { createReadStream } from 'fs';
import { parse } from 'csv-parse';
import { sql } from '../db/connection.js';
import { config } from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface CsvRow {
  dna_id: string;
  date_of_birth: string;
  age: string;
  gender: string;
  is_there_any_chance_you_might_be_pregnant_: string;
  nationality: string;
  father_s_city_of_origin: string;
  father_s_city_of_origin_1: string;
  city_of_residence_during_childhood: string;
  current_city_of_residence: string;
  consent_obtained_: string;
  date_of_enrolment: string;
  complete_: string;
  current_recent_smoker_1_year_: string;
  how_long_have_you_been_smoking_: string;
  how_many_cigarettes_have_you_been_smoking_a_day_: string;
  do_you_drink_alcohol_: string;
  do_you_take_any_medication_currently_: string;
  complete_1: string;
  volunteer_under_18_year_old_: string;
  non_egyptian_parents_: string;
  known_cvs_disease: string;
  known_collagen_disease: string;
  communication_difficulties: string;
  unwilling_to_participate: string;
  pregnant_female: string;
  contraindications_for_mri: string;
  history_of_sudden_death_history: string;
  history_of_familial_cardiomyopathies: string;
  history_of_premature_cad: string;
  complete_2: string;
  offspring_of_consanguinous_marriage: string;
  parents_occupation: string;
  marital_status: string;
  consanguinous_marriage: string;
  number_of_children: string;
  how_many_siblings_you_have_: string;
  are_you_one_of_a_twin_or_triplet_: string;
  who_and_what_disease_: string;
  does_any_other_non_cardiac_condition_run_in_your_family_: string;
  what_is_this_these_condition_s_: string;
  where_did_you_spend_your_childhood_: string;
  complete_3: string;
  heart_attack_or_angina: string;
  high_blood_pressure: string;
  dyslipidemia: string;
  rheumatic_fever: string;
  anaemia: string;
  lung_problems: string;
  kidney_problems: string;
  liver_problems: string;
  diabetes_mellitus: string;
  prior_heart_failure_previous_hx_: string;
  neurological_problems: string;
  muscloskeletal_problems: string;
  autoimmune_problems: string;
  have_you_undergone_an_operation_or_any_surgical_procedures_: string;
  procedure_details: string;
  malignancy: string;
  complete_4: string;
  examination_date: string;
  type: string;
  heart_rate: string;
  regularity: string;
  bp: string;
  height_cm_: string;
  weight_kg_: string;
  bmi: string;
  bsa: string;
  jvp: string;
  abnormal_physical_structure: string;
  s1: string;
  s2: string;
  s3: string;
  s4: string;
  complete_5: string;
  hba1c: string;
  troponin_i: string;
  complete_6: string;
  rate: string;
  rhythm: string;
  p_wave_abnormality: string;
  pr_interval: string;
  qrs_duration: string;
  qrs_abnormalities: string;
  st_segment_abnormalities: string;
  qtc_interval: string;
  t_wave_abnormalities: string;
  ecg_conclusion: string;
  complete_7: string;
  echo_date: string;
  aortic_root: string;
  left_atrium: string;
  right_ventricle: string;
  lvedd: string;
  lvesd: string;
  ivsd: string;
  ivss: string;
  lvpwd: string;
  lvpws: string;
  ef: string;
  fs: string;
  subaortic_membrane: string;
  mitral_regurge: string;
  mitral_stenosis: string;
  tricuspid_regurge: string;
  tricuspid_stenosis: string;
  aortic_regurge: string;
  aortic_stenosis: string;
  pulmonary_regurge: string;
  pulmonary_stenosis: string;
  complete_8: string;
  mri: string;
  heart_rate_during_mri: string;
  mri_date: string;
  left_ventricular_ejection_fraction: string;
  left_ventricular_end_diastolic_volume: string;
  left_ventricular_end_systolic_volume: string;
  left_ventricular_mass: string;
  right_ventricular_ef: string;
  complete_9: string;
  ever_smoked: string;
  smoking_years: string;
  current_city_category: string;
  childhood_city_category: string;
  migration_pattern: string;
  comorbidity: string;
  sysbp: string;
  diasbp: string;
  ecg_rate_clean: string;
  missing_ecg: string;
  missing_echo: string;
  missing_mri: string;
  missing_ecg_echo_mri: string;
  bp_outlier: string;
  hba1c_outlier: string;
  troponin_i_outlier: string;
  heart_rate_outlier: string;
  height_cm__outlier: string;
  weight_kg__outlier: string;
  bmi_outlier: string;
  bsa_outlier: string;
  sysbp_outlier: string;
  diasbp_outlier: string;
}

function parseBoolean(value: string | undefined): boolean {
  if (!value) return false;
  const v = value.trim().toLowerCase();
  return v === '1' || v === 'true' || v === 'yes';
}

function parseNumber(value: string | undefined): number | null {
  if (!value || value.trim() === '') return null;
  const num = parseFloat(value);
  return isNaN(num) ? null : num;
}

function parseInt2(value: string | undefined): number | null {
  if (!value || value.trim() === '') return null;
  const num = parseInt(value, 10);
  return isNaN(num) ? null : num;
}

function parseDate(value: string | undefined): string | null {
  if (!value || value.trim() === '') return null;
  // Handle different date formats
  const date = new Date(value);
  if (isNaN(date.getTime())) return null;
  return date.toISOString().split('T')[0];
}

async function importData() {
  const csvPath = join(__dirname, '../../../db/100925_Cleaned_EHVol_Data_STANDARDIZED.csv');
  
  console.log('🚀 Starting data import from:', csvPath);
  
  const records: CsvRow[] = [];
  
  // Parse CSV
  const parser = createReadStream(csvPath).pipe(
    parse({
      columns: true,
      skip_empty_lines: true,
      trim: true,
    })
  );
  
  for await (const record of parser) {
    records.push(record as CsvRow);
  }
  
  console.log(`📊 Parsed ${records.length} records from CSV`);
  
  let imported = 0;
  let errors = 0;
  
  for (const row of records) {
    try {
      // Insert patient
      const [patient] = await sql`
        INSERT INTO patients (
          dna_id, date_of_birth, age, gender, is_pregnant, nationality,
          father_city_origin, father_city_origin_alt, childhood_city,
          current_city, consent_obtained, enrollment_date, complete_status
        ) VALUES (
          ${row.dna_id},
          ${parseDate(row.date_of_birth)},
          ${parseInt2(row.age)},
          ${row.gender || null},
          ${parseBoolean(row.is_there_any_chance_you_might_be_pregnant_)},
          ${row.nationality || null},
          ${row.father_s_city_of_origin || null},
          ${row.father_s_city_of_origin_1 || null},
          ${row.city_of_residence_during_childhood || null},
          ${row.current_city_of_residence || null},
          ${parseBoolean(row.consent_obtained_)},
          ${parseDate(row.date_of_enrolment)},
          ${row.complete_ || null}
        )
        ON CONFLICT (dna_id) DO UPDATE SET
          age = EXCLUDED.age,
          updated_at = CURRENT_TIMESTAMP
        RETURNING id
      `;
      
      const patientId = patient.id;
      
      // Insert lifestyle data
      await sql`
        INSERT INTO lifestyle_data (
          patient_id, current_smoker, smoking_duration, cigarettes_per_day,
          drinks_alcohol, takes_medication, ever_smoked, smoking_years, complete_status
        ) VALUES (
          ${patientId},
          ${parseBoolean(row.current_recent_smoker_1_year_)},
          ${row.how_long_have_you_been_smoking_ || null},
          ${parseInt2(row.how_many_cigarettes_have_you_been_smoking_a_day_)},
          ${parseBoolean(row.do_you_drink_alcohol_)},
          ${parseBoolean(row.do_you_take_any_medication_currently_)},
          ${parseBoolean(row.ever_smoked)},
          ${parseNumber(row.smoking_years)},
          ${row.complete_1 || null}
        )
        ON CONFLICT DO NOTHING
      `;
      
      // Insert exclusion criteria
      await sql`
        INSERT INTO exclusion_criteria (
          patient_id, under_18, non_egyptian_parents, known_cvs_disease,
          known_collagen_disease, communication_difficulties, unwilling_to_participate,
          pregnant_female, contraindications_mri, history_sudden_death,
          history_familial_cardiomyopathies, history_premature_cad, complete_status
        ) VALUES (
          ${patientId},
          ${parseBoolean(row.volunteer_under_18_year_old_)},
          ${parseBoolean(row.non_egyptian_parents_)},
          ${parseBoolean(row.known_cvs_disease)},
          ${parseBoolean(row.known_collagen_disease)},
          ${parseBoolean(row.communication_difficulties)},
          ${parseBoolean(row.unwilling_to_participate)},
          ${parseBoolean(row.pregnant_female)},
          ${parseBoolean(row.contraindications_for_mri)},
          ${parseBoolean(row.history_of_sudden_death_history)},
          ${parseBoolean(row.history_of_familial_cardiomyopathies)},
          ${parseBoolean(row.history_of_premature_cad)},
          ${row.complete_2 || null}
        )
        ON CONFLICT DO NOTHING
      `;
      
      // Insert family history
      await sql`
        INSERT INTO family_history (
          patient_id, consanguinous_marriage_offspring, parents_occupation,
          marital_status, consanguinous_marriage, number_of_children,
          siblings_count, is_twin_or_triplet, family_disease_info,
          non_cardiac_condition_family, non_cardiac_condition_details,
          childhood_location, complete_status
        ) VALUES (
          ${patientId},
          ${parseBoolean(row.offspring_of_consanguinous_marriage)},
          ${row.parents_occupation || null},
          ${row.marital_status || null},
          ${parseBoolean(row.consanguinous_marriage)},
          ${parseInt2(row.number_of_children)},
          ${parseInt2(row.how_many_siblings_you_have_)},
          ${parseBoolean(row.are_you_one_of_a_twin_or_triplet_)},
          ${row.who_and_what_disease_ || null},
          ${parseBoolean(row.does_any_other_non_cardiac_condition_run_in_your_family_)},
          ${row.what_is_this_these_condition_s_ || null},
          ${row.where_did_you_spend_your_childhood_ || null},
          ${row.complete_3 || null}
        )
        ON CONFLICT DO NOTHING
      `;
      
      // Insert medical history
      await sql`
        INSERT INTO medical_history (
          patient_id, heart_attack_or_angina, high_blood_pressure, dyslipidemia,
          rheumatic_fever, anaemia, lung_problems, kidney_problems, liver_problems,
          diabetes_mellitus, prior_heart_failure, neurological_problems,
          musculoskeletal_problems, autoimmune_problems, undergone_surgery,
          procedure_details, malignancy, comorbidity, complete_status
        ) VALUES (
          ${patientId},
          ${parseBoolean(row.heart_attack_or_angina)},
          ${parseBoolean(row.high_blood_pressure)},
          ${parseBoolean(row.dyslipidemia)},
          ${parseBoolean(row.rheumatic_fever)},
          ${parseBoolean(row.anaemia)},
          ${parseBoolean(row.lung_problems)},
          ${parseBoolean(row.kidney_problems)},
          ${parseBoolean(row.liver_problems)},
          ${parseBoolean(row.diabetes_mellitus)},
          ${parseBoolean(row.prior_heart_failure_previous_hx_)},
          ${parseBoolean(row.neurological_problems)},
          ${parseBoolean(row.muscloskeletal_problems)},
          ${parseBoolean(row.autoimmune_problems)},
          ${parseBoolean(row.have_you_undergone_an_operation_or_any_surgical_procedures_)},
          ${row.procedure_details || null},
          ${parseBoolean(row.malignancy)},
          ${parseInt2(row.comorbidity) || 0},
          ${row.complete_4 || null}
        )
        ON CONFLICT DO NOTHING
      `;
      
      // Insert physical examinations
      await sql`
        INSERT INTO physical_examinations (
          patient_id, examination_date, examination_type, heart_rate, regularity,
          bp_reading, systolic_bp, diastolic_bp, height_cm, weight_kg, bmi, bsa, jvp,
          abnormal_physical_structure, s1, s2, s3, s4, complete_status,
          bp_outlier, height_outlier, weight_outlier, bmi_outlier, bsa_outlier,
          systolic_outlier, diastolic_outlier
        ) VALUES (
          ${patientId},
          ${parseDate(row.examination_date)},
          ${row.type || null},
          ${parseNumber(row.heart_rate)},
          ${row.regularity || null},
          ${row.bp || null},
          ${parseNumber(row.sysbp)},
          ${parseNumber(row.diasbp)},
          ${parseNumber(row.height_cm_)},
          ${parseNumber(row.weight_kg_)},
          ${parseNumber(row.bmi)},
          ${parseNumber(row.bsa)},
          ${parseNumber(row.jvp)},
          ${parseBoolean(row.abnormal_physical_structure)},
          ${row.s1 || null},
          ${row.s2 || null},
          ${parseBoolean(row.s3)},
          ${parseBoolean(row.s4)},
          ${row.complete_5 || null},
          ${parseBoolean(row.bp_outlier)},
          ${parseBoolean(row.height_cm__outlier)},
          ${parseBoolean(row.weight_kg__outlier)},
          ${parseBoolean(row.bmi_outlier)},
          ${parseBoolean(row.bsa_outlier)},
          ${parseBoolean(row.sysbp_outlier)},
          ${parseBoolean(row.diasbp_outlier)}
        )
        ON CONFLICT DO NOTHING
      `;
      
      // Insert lab results
      await sql`
        INSERT INTO lab_results (
          patient_id, hba1c, troponin_i, hba1c_outlier, troponin_outlier,
          heart_rate_outlier, complete_status
        ) VALUES (
          ${patientId},
          ${parseNumber(row.hba1c)},
          ${parseNumber(row.troponin_i)},
          ${parseBoolean(row.hba1c_outlier)},
          ${parseBoolean(row.troponin_i_outlier)},
          ${parseBoolean(row.heart_rate_outlier)},
          ${row.complete_6 || null}
        )
        ON CONFLICT DO NOTHING
      `;
      
      // Insert ECG data
      await sql`
        INSERT INTO ecg_data (
          patient_id, rate, rate_clean, rhythm, p_wave_abnormality, pr_interval,
          qrs_duration, qrs_abnormalities, st_segment_abnormalities, qtc_interval,
          t_wave_abnormalities, ecg_conclusion, missing_ecg, complete_status
        ) VALUES (
          ${patientId},
          ${parseNumber(row.rate)},
          ${parseNumber(row.ecg_rate_clean)},
          ${row.rhythm || null},
          ${parseBoolean(row.p_wave_abnormality)},
          ${parseNumber(row.pr_interval)},
          ${parseNumber(row.qrs_duration)},
          ${parseBoolean(row.qrs_abnormalities)},
          ${parseBoolean(row.st_segment_abnormalities)},
          ${parseNumber(row.qtc_interval)},
          ${parseBoolean(row.t_wave_abnormalities)},
          ${row.ecg_conclusion || null},
          ${parseBoolean(row.missing_ecg)},
          ${row.complete_7 || null}
        )
        ON CONFLICT DO NOTHING
      `;
      
      // Insert echo data
      await sql`
        INSERT INTO echo_data (
          patient_id, echo_date, aortic_root, left_atrium, right_ventricle,
          lvedd, lvesd, ivsd, ivss, lvpwd, lvpws, ef, fs, subaortic_membrane,
          mitral_regurge, mitral_stenosis, tricuspid_regurge, tricuspid_stenosis,
          aortic_regurge, aortic_stenosis, pulmonary_regurge, pulmonary_stenosis,
          missing_echo, complete_status
        ) VALUES (
          ${patientId},
          ${parseDate(row.echo_date)},
          ${parseNumber(row.aortic_root)},
          ${parseNumber(row.left_atrium)},
          ${parseNumber(row.right_ventricle)},
          ${parseNumber(row.lvedd)},
          ${parseNumber(row.lvesd)},
          ${parseNumber(row.ivsd)},
          ${parseNumber(row.ivss)},
          ${parseNumber(row.lvpwd)},
          ${parseNumber(row.lvpws)},
          ${parseNumber(row.ef)},
          ${parseNumber(row.fs)},
          ${parseBoolean(row.subaortic_membrane)},
          ${row.mitral_regurge || null},
          ${parseBoolean(row.mitral_stenosis)},
          ${row.tricuspid_regurge || null},
          ${parseBoolean(row.tricuspid_stenosis)},
          ${row.aortic_regurge || null},
          ${parseBoolean(row.aortic_stenosis)},
          ${row.pulmonary_regurge || null},
          ${parseBoolean(row.pulmonary_stenosis)},
          ${parseBoolean(row.missing_echo)},
          ${row.complete_8 || null}
        )
        ON CONFLICT DO NOTHING
      `;
      
      // Insert MRI data
      await sql`
        INSERT INTO mri_data (
          patient_id, mri_performed, heart_rate_during_mri, mri_date,
          lv_ejection_fraction, lv_end_diastolic_volume, lv_end_systolic_volume,
          lv_mass, rv_ejection_fraction, missing_mri, missing_ecg_echo_mri, complete_status
        ) VALUES (
          ${patientId},
          ${parseBoolean(row.mri)},
          ${parseNumber(row.heart_rate_during_mri)},
          ${parseDate(row.mri_date)},
          ${parseNumber(row.left_ventricular_ejection_fraction)},
          ${parseNumber(row.left_ventricular_end_diastolic_volume)},
          ${parseNumber(row.left_ventricular_end_systolic_volume)},
          ${parseNumber(row.left_ventricular_mass)},
          ${parseNumber(row.right_ventricular_ef)},
          ${parseBoolean(row.missing_mri)},
          ${parseBoolean(row.missing_ecg_echo_mri)},
          ${row.complete_9 || null}
        )
        ON CONFLICT DO NOTHING
      `;
      
      // Insert geographic data
      await sql`
        INSERT INTO geographic_data (
          patient_id, current_city_category, childhood_city_category, migration_pattern
        ) VALUES (
          ${patientId},
          ${row.current_city_category || null},
          ${row.childhood_city_category || null},
          ${row.migration_pattern || null}
        )
        ON CONFLICT DO NOTHING
      `;
      
      imported++;
      if (imported % 100 === 0) {
        console.log(`📦 Imported ${imported} records...`);
      }
    } catch (error) {
      errors++;
      console.error(`❌ Error importing record ${row.dna_id}:`, error);
    }
  }
  
  console.log(`\n✅ Import complete!`);
  console.log(`   - Successfully imported: ${imported}`);
  console.log(`   - Errors: ${errors}`);
  
  await sql.end();
}

importData().catch(console.error);
