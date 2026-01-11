import { Hono } from 'hono';
import { sql } from '../db/connection.js';

const cohort = new Hono();

interface CohortCriteria {
  ageMin?: number;
  ageMax?: number;
  gender?: string[];
  hasHypertension?: boolean;
  hasDiabetes?: boolean;
  hasDyslipidemia?: boolean;
  isSmoker?: boolean;
  bmiMin?: number;
  bmiMax?: number;
  efMin?: number;
  efMax?: number;
  hasEcho?: boolean;
  hasMri?: boolean;
  hasEcg?: boolean;
  minCompleteness?: number;
  cityCategory?: string[];
  migrationPattern?: string[];
}

// Build and execute cohort query
cohort.post('/query', async (c) => {
  try {
    const criteria: CohortCriteria = await c.req.json();
    
    let conditions: string[] = [];
    
    // Age criteria
    if (criteria.ageMin !== undefined) {
      conditions.push(`p.age >= ${criteria.ageMin}`);
    }
    if (criteria.ageMax !== undefined) {
      conditions.push(`p.age <= ${criteria.ageMax}`);
    }
    
    // Gender criteria
    if (criteria.gender && criteria.gender.length > 0) {
      conditions.push(`p.gender IN (${criteria.gender.map(g => `'${g}'`).join(',')})`);
    }
    
    // Medical history criteria
    if (criteria.hasHypertension !== undefined) {
      conditions.push(`mh.high_blood_pressure = ${criteria.hasHypertension}`);
    }
    if (criteria.hasDiabetes !== undefined) {
      conditions.push(`mh.diabetes_mellitus = ${criteria.hasDiabetes}`);
    }
    if (criteria.hasDyslipidemia !== undefined) {
      conditions.push(`mh.dyslipidemia = ${criteria.hasDyslipidemia}`);
    }
    
    // Lifestyle criteria
    if (criteria.isSmoker !== undefined) {
      conditions.push(`ld.current_smoker = ${criteria.isSmoker}`);
    }
    
    // BMI criteria
    if (criteria.bmiMin !== undefined) {
      conditions.push(`pe.bmi >= ${criteria.bmiMin}`);
    }
    if (criteria.bmiMax !== undefined) {
      conditions.push(`pe.bmi <= ${criteria.bmiMax}`);
    }
    
    // EF criteria
    if (criteria.efMin !== undefined) {
      conditions.push(`ed.ef >= ${criteria.efMin}`);
    }
    if (criteria.efMax !== undefined) {
      conditions.push(`ed.ef <= ${criteria.efMax}`);
    }
    
    // Data availability criteria
    if (criteria.hasEcho) {
      conditions.push(`ed.missing_echo = false`);
    }
    if (criteria.hasMri) {
      conditions.push(`md.missing_mri = false`);
    }
    if (criteria.hasEcg) {
      conditions.push(`ecg.missing_ecg = false`);
    }
    
    // Geographic criteria
    if (criteria.cityCategory && criteria.cityCategory.length > 0) {
      conditions.push(`gd.current_city_category IN (${criteria.cityCategory.map(c => `'${c}'`).join(',')})`);
    }
    if (criteria.migrationPattern && criteria.migrationPattern.length > 0) {
      conditions.push(`gd.migration_pattern IN (${criteria.migrationPattern.map(m => `'${m}'`).join(',')})`);
    }
    
    const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    
    // Get matching patients
    const patients = await sql.unsafe(`
      SELECT DISTINCT
        p.id,
        p.dna_id,
        p.age,
        p.gender,
        p.nationality,
        p.enrollment_date,
        pe.bmi,
        pe.systolic_bp,
        pe.diastolic_bp,
        lr.hba1c,
        ed.ef as echo_ef,
        md.lv_ejection_fraction as mri_ef,
        mh.diabetes_mellitus,
        mh.high_blood_pressure,
        ld.current_smoker,
        gd.current_city_category,
        (
          (CASE WHEN pe.id IS NOT NULL THEN 20 ELSE 0 END) +
          (CASE WHEN lr.id IS NOT NULL THEN 20 ELSE 0 END) +
          (CASE WHEN ecg.id IS NOT NULL THEN 20 ELSE 0 END) +
          (CASE WHEN ed.id IS NOT NULL AND ed.missing_echo = FALSE THEN 20 ELSE 0 END) +
          (CASE WHEN md.id IS NOT NULL AND md.missing_mri = FALSE THEN 20 ELSE 0 END)
        ) as data_completeness
      FROM patients p
      LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
      LEFT JOIN lab_results lr ON p.id = lr.patient_id
      LEFT JOIN ecg_data ecg ON p.id = ecg.patient_id
      LEFT JOIN echo_data ed ON p.id = ed.patient_id
      LEFT JOIN mri_data md ON p.id = md.patient_id
      LEFT JOIN medical_history mh ON p.id = mh.patient_id
      LEFT JOIN lifestyle_data ld ON p.id = ld.patient_id
      LEFT JOIN geographic_data gd ON p.id = gd.patient_id
      ${whereClause}
      ${criteria.minCompleteness ? `HAVING (
        (CASE WHEN pe.id IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN lr.id IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN ecg.id IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN ed.id IS NOT NULL AND ed.missing_echo = FALSE THEN 20 ELSE 0 END) +
        (CASE WHEN md.id IS NOT NULL AND md.missing_mri = FALSE THEN 20 ELSE 0 END)
      ) >= ${criteria.minCompleteness}` : ''}
      ORDER BY p.dna_id
      LIMIT 500
    `);
    
    // Get count
    const [countResult] = await sql.unsafe(`
      SELECT COUNT(DISTINCT p.id) as total
      FROM patients p
      LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
      LEFT JOIN lab_results lr ON p.id = lr.patient_id
      LEFT JOIN ecg_data ecg ON p.id = ecg.patient_id
      LEFT JOIN echo_data ed ON p.id = ed.patient_id
      LEFT JOIN mri_data md ON p.id = md.patient_id
      LEFT JOIN medical_history mh ON p.id = mh.patient_id
      LEFT JOIN lifestyle_data ld ON p.id = ld.patient_id
      LEFT JOIN geographic_data gd ON p.id = gd.patient_id
      ${whereClause}
    `);

    return c.json({
      success: true,
      data: {
        patients,
        totalCount: parseInt(countResult.total),
        criteria
      }
    });
  } catch (error) {
    console.error('Error executing cohort query:', error);
    return c.json({ success: false, error: 'Cohort query failed' }, 500);
  }
});

// Get cohort summary statistics
cohort.post('/summary', async (c) => {
  try {
    const { patientIds } = await c.req.json();
    
    if (!patientIds || patientIds.length === 0) {
      return c.json({ success: false, error: 'No patients specified' }, 400);
    }
    
    const idList = patientIds.join(',');
    
    const [demographics] = await sql.unsafe(`
      SELECT 
        COUNT(*) as total,
        AVG(age) as avg_age,
        MIN(age) as min_age,
        MAX(age) as max_age,
        COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male_count,
        COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female_count
      FROM patients
      WHERE id IN (${idList})
    `);
    
    const [clinical] = await sql.unsafe(`
      SELECT 
        AVG(pe.bmi) as avg_bmi,
        AVG(pe.systolic_bp) as avg_sbp,
        AVG(pe.diastolic_bp) as avg_dbp,
        AVG(lr.hba1c) as avg_hba1c,
        AVG(ed.ef) as avg_ef
      FROM patients p
      LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
      LEFT JOIN lab_results lr ON p.id = lr.patient_id
      LEFT JOIN echo_data ed ON p.id = ed.patient_id
      WHERE p.id IN (${idList})
    `);
    
    const [conditions] = await sql.unsafe(`
      SELECT 
        SUM(CASE WHEN high_blood_pressure THEN 1 ELSE 0 END) as hypertension,
        SUM(CASE WHEN diabetes_mellitus THEN 1 ELSE 0 END) as diabetes,
        SUM(CASE WHEN dyslipidemia THEN 1 ELSE 0 END) as dyslipidemia
      FROM medical_history
      WHERE patient_id IN (${idList})
    `);

    return c.json({
      success: true,
      data: {
        demographics,
        clinical,
        conditions
      }
    });
  } catch (error) {
    console.error('Error getting cohort summary:', error);
    return c.json({ success: false, error: 'Failed to get cohort summary' }, 500);
  }
});

// Export cohort data as CSV
cohort.post('/export', async (c) => {
  try {
    const { patientIds, fields } = await c.req.json();
    
    if (!patientIds || patientIds.length === 0) {
      return c.json({ success: false, error: 'No patients specified' }, 400);
    }
    
    const idList = patientIds.join(',');
    
    const data = await sql.unsafe(`
      SELECT 
        p.dna_id,
        p.age,
        p.gender,
        p.nationality,
        p.enrollment_date,
        pe.bmi,
        pe.systolic_bp,
        pe.diastolic_bp,
        pe.heart_rate,
        lr.hba1c,
        lr.troponin_i,
        ed.ef as echo_ef,
        md.lv_ejection_fraction as mri_ef,
        md.lv_mass,
        mh.diabetes_mellitus,
        mh.high_blood_pressure,
        mh.dyslipidemia,
        ld.current_smoker,
        ld.smoking_years,
        gd.current_city_category,
        gd.migration_pattern
      FROM patients p
      LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
      LEFT JOIN lab_results lr ON p.id = lr.patient_id
      LEFT JOIN echo_data ed ON p.id = ed.patient_id
      LEFT JOIN mri_data md ON p.id = md.patient_id
      LEFT JOIN medical_history mh ON p.id = mh.patient_id
      LEFT JOIN lifestyle_data ld ON p.id = ld.patient_id
      LEFT JOIN geographic_data gd ON p.id = gd.patient_id
      WHERE p.id IN (${idList})
    `);

    return c.json({
      success: true,
      data
    });
  } catch (error) {
    console.error('Error exporting cohort:', error);
    return c.json({ success: false, error: 'Failed to export cohort' }, 500);
  }
});

export default cohort;
