import { Hono } from 'hono';
import { sql } from '../db/connection.js';

const patients = new Hono();

// Get all patients with pagination and filtering
patients.get('/', async (c) => {
  try {
    const page = parseInt(c.req.query('page') || '1');
    const limit = parseInt(c.req.query('limit') || '50');
    const offset = (page - 1) * limit;
    const search = c.req.query('search') || '';
    const gender = c.req.query('gender') || '';
    const ageMin = c.req.query('ageMin') || '';
    const ageMax = c.req.query('ageMax') || '';
    const sortBy = c.req.query('sortBy') || 'dna_id';
    const sortOrder = c.req.query('sortOrder') === 'desc' ? 'DESC' : 'ASC';
    
    // Additional filters for cohort builder
    const hasEcho = c.req.query('hasEcho');
    const hasMri = c.req.query('hasMri');
    const hasGenomics = c.req.query('hasGenomics');
    const hasLabs = c.req.query('hasLabs');
    const hasImaging = c.req.query('hasImaging');
    const minDataCompleteness = c.req.query('minDataCompleteness');
    const nationality = c.req.query('nationality');
    const enrollmentDateFrom = c.req.query('enrollmentDateFrom');
    const enrollmentDateTo = c.req.query('enrollmentDateTo');
    const region = c.req.query('region');
    
    // Clinical filters
    const hasDiabetes = c.req.query('hasDiabetes');
    const hasHypertension = c.req.query('hasHypertension');
    const hasSmoking = c.req.query('hasSmoking');
    const hasObesity = c.req.query('hasObesity');
    const hasFamilyHistory = c.req.query('hasFamilyHistory');

    // Build dynamic query
    let whereConditions: string[] = [];
    let havingConditions: string[] = [];
    
    if (search) {
      whereConditions.push(`(p.dna_id ILIKE '%${search}%' OR p.nationality ILIKE '%${search}%' OR p.current_city ILIKE '%${search}%')`);
    }
    if (gender) {
      whereConditions.push(`p.gender = '${gender}'`);
    }
    if (ageMin) {
      whereConditions.push(`p.age >= ${parseInt(ageMin)}`);
    }
    if (ageMax) {
      whereConditions.push(`p.age <= ${parseInt(ageMax)}`);
    }
    
    // Data availability filters
    if (hasEcho === 'true') {
      whereConditions.push(`ed.missing_echo = false`);
    }
    if (hasMri === 'true') {
      whereConditions.push(`md.missing_mri = false`);
    }
    if (hasGenomics === 'true') {
      whereConditions.push(`lr.id IS NOT NULL`);
    }
    if (hasLabs === 'true') {
      whereConditions.push(`lr.id IS NOT NULL`);
    }
    if (hasImaging === 'true') {
      whereConditions.push(`(ed.missing_echo = false OR md.missing_mri = false)`);
    }
    
    // Geographic/nationality filters
    if (nationality) {
      whereConditions.push(`p.nationality ILIKE '%${nationality}%'`);
    }
    if (region) {
      whereConditions.push(`gd.current_city_category ILIKE '%${region}%'`);
    }
    
    // Temporal filters
    if (enrollmentDateFrom) {
      whereConditions.push(`p.enrollment_date >= '${enrollmentDateFrom}'`);
    }
    if (enrollmentDateTo) {
      whereConditions.push(`p.enrollment_date <= '${enrollmentDateTo}'`);
    }
    
    // Clinical/risk factor filters
    if (hasDiabetes === 'true') {
      whereConditions.push(`mh.diabetes_mellitus = true`);
    }
    if (hasHypertension === 'true') {
      whereConditions.push(`mh.high_blood_pressure = true`);
    }
    if (hasSmoking === 'true') {
      whereConditions.push(`ld.current_smoker = true`);
    }
    if (hasObesity === 'true') {
      whereConditions.push(`pe.bmi >= 30`);
    }
    if (hasFamilyHistory === 'true') {
      // Family history of CVD - check for relevant family disease info
      whereConditions.push(`fh.family_disease_info IS NOT NULL`);
    }

    const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';

    const patients = await sql.unsafe(`
      SELECT 
        p.id,
        p.dna_id,
        p.age,
        p.gender,
        p.nationality,
        p.enrollment_date,
        p.current_city,
        pe.heart_rate,
        pe.systolic_bp,
        pe.diastolic_bp,
        pe.bmi,
        lr.hba1c,
        ed.ef as echo_ef,
        md.lv_ejection_fraction as mri_ef,
        gd.current_city_category,
        mh.diabetes_mellitus,
        mh.high_blood_pressure,
        ld.current_smoker as smoking,
        fh.family_disease_info as family_history_info,
        CASE 
          WHEN md.missing_mri = false THEN true ELSE false 
        END as has_mri,
        CASE 
          WHEN ed.missing_echo = false THEN true ELSE false 
        END as has_echo,
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
      LEFT JOIN geographic_data gd ON p.id = gd.patient_id
      LEFT JOIN medical_history mh ON p.id = mh.patient_id
      LEFT JOIN lifestyle_data ld ON p.id = ld.patient_id
      LEFT JOIN family_history fh ON p.id = fh.patient_id
      ${whereClause}
      ORDER BY ${sortBy === 'data_completeness' ? 'data_completeness' : `p.${sortBy}`} ${sortOrder}
      LIMIT ${limit} OFFSET ${offset}
    `);

    const [countResult] = await sql.unsafe(`
      SELECT COUNT(DISTINCT p.id) as total 
      FROM patients p
      LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
      LEFT JOIN lab_results lr ON p.id = lr.patient_id
      LEFT JOIN ecg_data ecg ON p.id = ecg.patient_id
      LEFT JOIN echo_data ed ON p.id = ed.patient_id
      LEFT JOIN mri_data md ON p.id = md.patient_id
      LEFT JOIN geographic_data gd ON p.id = gd.patient_id
      LEFT JOIN medical_history mh ON p.id = mh.patient_id
      LEFT JOIN lifestyle_data ld ON p.id = ld.patient_id
      LEFT JOIN family_history fh ON p.id = fh.patient_id
      ${whereClause}
    `);

    return c.json({
      success: true,
      data: patients,
      pagination: {
        page,
        limit,
        total: parseInt(countResult.total),
        totalPages: Math.ceil(parseInt(countResult.total) / limit)
      }
    });
  } catch (error) {
    console.error('Error fetching patients:', error);
    return c.json({ success: false, error: 'Failed to fetch patients' }, 500);
  }
});

// Get single patient by DNA ID
patients.get('/:dnaId', async (c) => {
  try {
    const dnaId = c.req.param('dnaId');
    
    const [patient] = await sql`
      SELECT * FROM patients WHERE dna_id = ${dnaId}
    `;
    
    if (!patient) {
      return c.json({ success: false, error: 'Patient not found' }, 404);
    }

    // Get all related data
    const [lifestyle] = await sql`SELECT * FROM lifestyle_data WHERE patient_id = ${patient.id}`;
    const [exclusion] = await sql`SELECT * FROM exclusion_criteria WHERE patient_id = ${patient.id}`;
    const [family] = await sql`SELECT * FROM family_history WHERE patient_id = ${patient.id}`;
    const [medical] = await sql`SELECT * FROM medical_history WHERE patient_id = ${patient.id}`;
    const [physical] = await sql`SELECT * FROM physical_examinations WHERE patient_id = ${patient.id}`;
    const [labs] = await sql`SELECT * FROM lab_results WHERE patient_id = ${patient.id}`;
    const [ecg] = await sql`SELECT * FROM ecg_data WHERE patient_id = ${patient.id}`;
    const [echo] = await sql`SELECT * FROM echo_data WHERE patient_id = ${patient.id}`;
    const [mri] = await sql`SELECT * FROM mri_data WHERE patient_id = ${patient.id}`;
    const [geographic] = await sql`SELECT * FROM geographic_data WHERE patient_id = ${patient.id}`;

    return c.json({
      success: true,
      data: {
        ...patient,
        lifestyle,
        exclusion,
        family,
        medical,
        physical,
        labs,
        ecg,
        echo,
        mri,
        geographic
      }
    });
  } catch (error) {
    console.error('Error fetching patient:', error);
    return c.json({ success: false, error: 'Failed to fetch patient' }, 500);
  }
});

// Search patients
patients.get('/search/:query', async (c) => {
  try {
    const query = c.req.param('query');
    const limit = parseInt(c.req.query('limit') || '20');
    
    const results = await sql`
      SELECT 
        p.id,
        p.dna_id,
        p.age,
        p.gender,
        p.nationality,
        p.current_city,
        pe.bmi,
        mh.high_blood_pressure,
        mh.diabetes_mellitus
      FROM patients p
      LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
      LEFT JOIN medical_history mh ON p.id = mh.patient_id
      WHERE 
        p.dna_id ILIKE ${'%' + query + '%'}
        OR p.nationality ILIKE ${'%' + query + '%'}
        OR p.current_city ILIKE ${'%' + query + '%'}
      LIMIT ${limit}
    `;

    return c.json({ success: true, data: results });
  } catch (error) {
    console.error('Error searching patients:', error);
    return c.json({ success: false, error: 'Search failed' }, 500);
  }
});

// Get patient vitals
patients.get('/:dnaId/vitals', async (c) => {
  try {
    const dnaId = c.req.param('dnaId');
    
    const [patient] = await sql`SELECT id FROM patients WHERE dna_id = ${dnaId}`;
    if (!patient) {
      return c.json({ success: false, error: 'Patient not found' }, 404);
    }

    const [physical] = await sql`
      SELECT * FROM physical_examinations WHERE patient_id = ${patient.id}
    `;
    const [labs] = await sql`
      SELECT * FROM lab_results WHERE patient_id = ${patient.id}
    `;

    return c.json({
      success: true,
      data: {
        current: {
          systolic: physical?.systolic_bp,
          diastolic: physical?.diastolic_bp,
          heartRate: physical?.heart_rate,
          weight: physical?.weight_kg,
          height: physical?.height_cm,
          bmi: physical?.bmi,
          bsa: physical?.bsa,
          hba1c: labs?.hba1c,
          troponin: labs?.troponin_i
        }
      }
    });
  } catch (error) {
    console.error('Error fetching vitals:', error);
    return c.json({ success: false, error: 'Failed to fetch vitals' }, 500);
  }
});

// Get patient imaging data (echo + MRI)
patients.get('/:dnaId/imaging', async (c) => {
  try {
    const dnaId = c.req.param('dnaId');
    
    const [patient] = await sql`SELECT id FROM patients WHERE dna_id = ${dnaId}`;
    if (!patient) {
      return c.json({ success: false, error: 'Patient not found' }, 404);
    }

    const [echo] = await sql`SELECT * FROM echo_data WHERE patient_id = ${patient.id}`;
    const [mri] = await sql`SELECT * FROM mri_data WHERE patient_id = ${patient.id}`;

    return c.json({
      success: true,
      data: { echo, mri }
    });
  } catch (error) {
    console.error('Error fetching imaging:', error);
    return c.json({ success: false, error: 'Failed to fetch imaging data' }, 500);
  }
});

// Get patient risk factors
patients.get('/:dnaId/risk-factors', async (c) => {
  try {
    const dnaId = c.req.param('dnaId');
    
    const results = await sql`
      SELECT * FROM risk_factors_summary WHERE dna_id = ${dnaId}
    `;

    if (results.length === 0) {
      return c.json({ success: false, error: 'Patient not found' }, 404);
    }

    return c.json({ success: true, data: results[0] });
  } catch (error) {
    console.error('Error fetching risk factors:', error);
    return c.json({ success: false, error: 'Failed to fetch risk factors' }, 500);
  }
});

export default patients;
