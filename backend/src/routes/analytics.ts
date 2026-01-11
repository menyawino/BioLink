import { Hono } from 'hono';
import { sql } from '../db/connection.js';

const analytics = new Hono();

// Get registry overview stats
analytics.get('/overview', async (c) => {
  try {
    const [totalPatients] = await sql`SELECT COUNT(*) as total FROM patients`;
    const [genderStats] = await sql`
      SELECT 
        COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male,
        COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female
      FROM patients
    `;
    const [avgAge] = await sql`SELECT AVG(age) as avg_age FROM patients WHERE age IS NOT NULL`;
    const [completeness] = await sql`
      SELECT AVG(completeness_score) as avg_completeness FROM data_completeness
    `;
    const [withMri] = await sql`SELECT COUNT(*) as count FROM mri_data WHERE missing_mri = false`;
    const [withEcho] = await sql`SELECT COUNT(*) as count FROM echo_data WHERE missing_echo = false`;
    const [withEcg] = await sql`SELECT COUNT(*) as count FROM ecg_data WHERE missing_ecg = false`;

    return c.json({
      success: true,
      data: {
        totalPatients: parseInt(totalPatients.total),
        maleCount: parseInt(genderStats.male),
        femaleCount: parseInt(genderStats.female),
        averageAge: parseFloat(avgAge.avg_age).toFixed(1),
        dataCompleteness: parseFloat(completeness.avg_completeness).toFixed(1),
        withMri: parseInt(withMri.count),
        withEcho: parseInt(withEcho.count),
        withEcg: parseInt(withEcg.count)
      }
    });
  } catch (error) {
    console.error('Error fetching overview:', error);
    return c.json({ success: false, error: 'Failed to fetch overview' }, 500);
  }
});

// Get demographics breakdown
analytics.get('/demographics', async (c) => {
  try {
    const ageGender = await sql`
      SELECT 
        CASE 
          WHEN age < 30 THEN '18-29'
          WHEN age BETWEEN 30 AND 39 THEN '30-39'
          WHEN age BETWEEN 40 AND 49 THEN '40-49'
          WHEN age BETWEEN 50 AND 59 THEN '50-59'
          WHEN age BETWEEN 60 AND 69 THEN '60-69'
          WHEN age >= 70 THEN '70+'
        END as age_group,
        COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male,
        COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female
      FROM patients
      WHERE age IS NOT NULL
      GROUP BY age_group
      ORDER BY age_group
    `;

    const nationality = await sql`
      SELECT nationality, COUNT(*) as count
      FROM patients
      WHERE nationality IS NOT NULL
      GROUP BY nationality
      ORDER BY count DESC
      LIMIT 10
    `;

    const maritalStatus = await sql`
      SELECT marital_status, COUNT(*) as count
      FROM family_history
      WHERE marital_status IS NOT NULL
      GROUP BY marital_status
      ORDER BY count DESC
    `;

    return c.json({
      success: true,
      data: {
        ageGender,
        nationality,
        maritalStatus
      }
    });
  } catch (error) {
    console.error('Error fetching demographics:', error);
    return c.json({ success: false, error: 'Failed to fetch demographics' }, 500);
  }
});

// Get clinical metrics distribution
analytics.get('/clinical', async (c) => {
  try {
    const bmiDistribution = await sql`
      SELECT 
        CASE
          WHEN bmi < 18.5 THEN 'Underweight'
          WHEN bmi BETWEEN 18.5 AND 24.9 THEN 'Normal'
          WHEN bmi BETWEEN 25 AND 29.9 THEN 'Overweight'
          WHEN bmi >= 30 THEN 'Obese'
        END as category,
        COUNT(*) as count
      FROM physical_examinations
      WHERE bmi IS NOT NULL
      GROUP BY category
    `;

    const bpDistribution = await sql`
      SELECT 
        CASE 
          WHEN systolic_bp >= 140 OR diastolic_bp >= 90 THEN 'High'
          WHEN systolic_bp >= 120 OR diastolic_bp >= 80 THEN 'Elevated'
          ELSE 'Normal'
        END as status,
        COUNT(*) as count
      FROM physical_examinations
      WHERE systolic_bp IS NOT NULL
      GROUP BY status
    `;

    const efDistribution = await sql`
      SELECT 
        CASE 
          WHEN ef >= 55 THEN 'Normal (≥55%)'
          WHEN ef BETWEEN 40 AND 54 THEN 'Mildly Reduced (40-54%)'
          WHEN ef BETWEEN 30 AND 39 THEN 'Moderately Reduced (30-39%)'
          WHEN ef < 30 THEN 'Severely Reduced (<30%)'
        END as category,
        COUNT(*) as count
      FROM echo_data
      WHERE ef IS NOT NULL
      GROUP BY category
    `;

    const hba1cDistribution = await sql`
      SELECT 
        CASE 
          WHEN hba1c < 5.7 THEN 'Normal (<5.7%)'
          WHEN hba1c BETWEEN 5.7 AND 6.4 THEN 'Prediabetes (5.7-6.4%)'
          WHEN hba1c >= 6.5 THEN 'Diabetes (≥6.5%)'
        END as category,
        COUNT(*) as count
      FROM lab_results
      WHERE hba1c IS NOT NULL
      GROUP BY category
    `;

    return c.json({
      success: true,
      data: {
        bmiDistribution,
        bpDistribution,
        efDistribution,
        hba1cDistribution
      }
    });
  } catch (error) {
    console.error('Error fetching clinical metrics:', error);
    return c.json({ success: false, error: 'Failed to fetch clinical metrics' }, 500);
  }
});

// Get comorbidity analysis
analytics.get('/comorbidities', async (c) => {
  try {
    const conditions = await sql`
      SELECT 
        SUM(CASE WHEN high_blood_pressure THEN 1 ELSE 0 END) as hypertension,
        SUM(CASE WHEN diabetes_mellitus THEN 1 ELSE 0 END) as diabetes,
        SUM(CASE WHEN dyslipidemia THEN 1 ELSE 0 END) as dyslipidemia,
        SUM(CASE WHEN heart_attack_or_angina THEN 1 ELSE 0 END) as cad,
        SUM(CASE WHEN prior_heart_failure THEN 1 ELSE 0 END) as heart_failure,
        SUM(CASE WHEN lung_problems THEN 1 ELSE 0 END) as lung_disease,
        SUM(CASE WHEN kidney_problems THEN 1 ELSE 0 END) as kidney_disease,
        SUM(CASE WHEN neurological_problems THEN 1 ELSE 0 END) as neurological
      FROM medical_history
    `;

    const comorbidityCount = await sql`
      SELECT comorbidity, COUNT(*) as count
      FROM medical_history
      GROUP BY comorbidity
      ORDER BY comorbidity
    `;

    return c.json({
      success: true,
      data: {
        conditions: conditions[0],
        comorbidityDistribution: comorbidityCount
      }
    });
  } catch (error) {
    console.error('Error fetching comorbidities:', error);
    return c.json({ success: false, error: 'Failed to fetch comorbidities' }, 500);
  }
});

// Get smoking/lifestyle statistics
analytics.get('/lifestyle', async (c) => {
  try {
    const smoking = await sql`
      SELECT 
        SUM(CASE WHEN current_smoker THEN 1 ELSE 0 END) as current_smokers,
        SUM(CASE WHEN ever_smoked AND NOT current_smoker THEN 1 ELSE 0 END) as former_smokers,
        SUM(CASE WHEN NOT ever_smoked THEN 1 ELSE 0 END) as never_smoked
      FROM lifestyle_data
    `;

    const smokingYears = await sql`
      SELECT 
        CASE 
          WHEN smoking_years < 5 THEN '<5 years'
          WHEN smoking_years BETWEEN 5 AND 10 THEN '5-10 years'
          WHEN smoking_years BETWEEN 10 AND 20 THEN '10-20 years'
          WHEN smoking_years > 20 THEN '>20 years'
        END as duration,
        COUNT(*) as count
      FROM lifestyle_data
      WHERE smoking_years IS NOT NULL AND smoking_years > 0
      GROUP BY duration
    `;

    return c.json({
      success: true,
      data: {
        smoking: smoking[0],
        smokingDuration: smokingYears
      }
    });
  } catch (error) {
    console.error('Error fetching lifestyle data:', error);
    return c.json({ success: false, error: 'Failed to fetch lifestyle data' }, 500);
  }
});

// Get geographic distribution
analytics.get('/geographic', async (c) => {
  try {
    const cityCategory = await sql`
      SELECT current_city_category, COUNT(*) as count
      FROM geographic_data
      WHERE current_city_category IS NOT NULL
      GROUP BY current_city_category
    `;

    const migration = await sql`
      SELECT migration_pattern, COUNT(*) as count
      FROM geographic_data
      WHERE migration_pattern IS NOT NULL
      GROUP BY migration_pattern
      ORDER BY count DESC
    `;

    const cityDistribution = await sql`
      SELECT 
        p.current_city,
        COUNT(*) as count,
        AVG(p.age) as avg_age
      FROM patients p
      WHERE p.current_city IS NOT NULL
      GROUP BY p.current_city
      ORDER BY count DESC
      LIMIT 15
    `;

    return c.json({
      success: true,
      data: {
        cityCategory,
        migration,
        cityDistribution
      }
    });
  } catch (error) {
    console.error('Error fetching geographic data:', error);
    return c.json({ success: false, error: 'Failed to fetch geographic data' }, 500);
  }
});

// Get enrollment trends
analytics.get('/enrollment-trends', async (c) => {
  try {
    const trends = await sql`
      SELECT 
        TO_CHAR(enrollment_date, 'YYYY-MM') as month,
        COUNT(*) as enrolled
      FROM patients
      WHERE enrollment_date IS NOT NULL
      GROUP BY TO_CHAR(enrollment_date, 'YYYY-MM')
      ORDER BY month
    `;

    // Calculate cumulative
    let cumulative = 0;
    const trendsWithCumulative = trends.map(t => {
      cumulative += parseInt(t.enrolled);
      return {
        ...t,
        cumulative
      };
    });

    return c.json({
      success: true,
      data: trendsWithCumulative
    });
  } catch (error) {
    console.error('Error fetching enrollment trends:', error);
    return c.json({ success: false, error: 'Failed to fetch enrollment trends' }, 500);
  }
});

// Get data completeness analysis
analytics.get('/data-quality', async (c) => {
  try {
    const completeness = await sql`
      SELECT 
        AVG(CASE WHEN has_physical_exam THEN 100 ELSE 0 END) as physical_exam,
        AVG(CASE WHEN has_lab_results THEN 100 ELSE 0 END) as lab_results,
        AVG(CASE WHEN has_ecg THEN 100 ELSE 0 END) as ecg,
        AVG(CASE WHEN has_echo THEN 100 ELSE 0 END) as echo,
        AVG(CASE WHEN has_mri THEN 100 ELSE 0 END) as mri,
        AVG(completeness_score) as overall
      FROM data_completeness
    `;

    const completenessDistribution = await sql`
      SELECT 
        CASE 
          WHEN completeness_score >= 80 THEN 'Complete (≥80%)'
          WHEN completeness_score >= 60 THEN 'Partial (60-79%)'
          WHEN completeness_score >= 40 THEN 'Limited (40-59%)'
          ELSE 'Minimal (<40%)'
        END as category,
        COUNT(*) as count
      FROM data_completeness
      GROUP BY category
    `;

    return c.json({
      success: true,
      data: {
        byCategory: completeness[0],
        distribution: completenessDistribution
      }
    });
  } catch (error) {
    console.error('Error fetching data quality:', error);
    return c.json({ success: false, error: 'Failed to fetch data quality' }, 500);
  }
});

// Get imaging statistics
analytics.get('/imaging', async (c) => {
  try {
    const echoStats = await sql`
      SELECT 
        AVG(ef) as avg_ef,
        MIN(ef) as min_ef,
        MAX(ef) as max_ef,
        STDDEV(ef) as std_ef,
        COUNT(*) as total
      FROM echo_data
      WHERE ef IS NOT NULL AND missing_echo = false
    `;

    const mriStats = await sql`
      SELECT 
        AVG(lv_ejection_fraction) as avg_lv_ef,
        AVG(lv_mass) as avg_lv_mass,
        AVG(lv_end_diastolic_volume) as avg_lv_edv,
        COUNT(*) as total
      FROM mri_data
      WHERE lv_ejection_fraction IS NOT NULL AND missing_mri = false
    `;

    return c.json({
      success: true,
      data: {
        echo: echoStats[0],
        mri: mriStats[0]
      }
    });
  } catch (error) {
    console.error('Error fetching imaging stats:', error);
    return c.json({ success: false, error: 'Failed to fetch imaging stats' }, 500);
  }
});

// ECG analysis
analytics.get('/ecg', async (c) => {
  try {
    const conclusions = await sql`
      SELECT ecg_conclusion, COUNT(*) as count
      FROM ecg_data
      WHERE ecg_conclusion IS NOT NULL
      GROUP BY ecg_conclusion
      ORDER BY count DESC
    `;

    const abnormalities = await sql`
      SELECT 
        SUM(CASE WHEN p_wave_abnormality THEN 1 ELSE 0 END) as p_wave,
        SUM(CASE WHEN qrs_abnormalities THEN 1 ELSE 0 END) as qrs,
        SUM(CASE WHEN st_segment_abnormalities THEN 1 ELSE 0 END) as st_segment,
        SUM(CASE WHEN t_wave_abnormalities THEN 1 ELSE 0 END) as t_wave
      FROM ecg_data
    `;

    const rhythmDistribution = await sql`
      SELECT rhythm, COUNT(*) as count
      FROM ecg_data
      WHERE rhythm IS NOT NULL
      GROUP BY rhythm
    `;

    return c.json({
      success: true,
      data: {
        conclusions,
        abnormalities: abnormalities[0],
        rhythmDistribution
      }
    });
  } catch (error) {
    console.error('Error fetching ECG analysis:', error);
    return c.json({ success: false, error: 'Failed to fetch ECG analysis' }, 500);
  }
});

// Get enrollment trends over time
analytics.get('/enrollment-trends', async (c) => {
  try {
    const trends = await sql`
      SELECT 
        TO_CHAR(enrollment_date, 'Mon YYYY') as month,
        COUNT(*) as enrolled,
        SUM(COUNT(*)) OVER (ORDER BY DATE_TRUNC('month', enrollment_date)) as cumulative
      FROM patients
      WHERE enrollment_date IS NOT NULL
      GROUP BY DATE_TRUNC('month', enrollment_date), TO_CHAR(enrollment_date, 'Mon YYYY')
      ORDER BY DATE_TRUNC('month', enrollment_date)
    `;

    return c.json({
      success: true,
      data: trends
    });
  } catch (error) {
    console.error('Error fetching enrollment trends:', error);
    return c.json({ success: false, error: 'Failed to fetch enrollment trends' }, 500);
  }
});

// Get data intersection statistics (patients with multiple data types)
analytics.get('/data-intersections', async (c) => {
  try {
    const intersections = await sql`
      WITH patient_data AS (
        SELECT 
          p.patient_id,
          CASE WHEN e.patient_id IS NOT NULL AND NOT e.missing_echo THEN 1 ELSE 0 END as has_echo,
          CASE WHEN m.patient_id IS NOT NULL AND NOT m.missing_mri THEN 1 ELSE 0 END as has_mri,
          CASE WHEN ec.patient_id IS NOT NULL AND NOT ec.missing_ecg THEN 1 ELSE 0 END as has_ecg
        FROM patients p
        LEFT JOIN echo_data e ON p.patient_id = e.patient_id
        LEFT JOIN mri_data m ON p.patient_id = m.patient_id
        LEFT JOIN ecg_data ec ON p.patient_id = ec.patient_id
      )
      SELECT 
        CASE 
          WHEN has_echo = 1 AND has_mri = 0 AND has_ecg = 0 THEN 'Echo Only'
          WHEN has_echo = 0 AND has_mri = 1 AND has_ecg = 0 THEN 'MRI Only'
          WHEN has_echo = 0 AND has_mri = 0 AND has_ecg = 1 THEN 'ECG Only'
          WHEN has_echo = 1 AND has_mri = 1 AND has_ecg = 0 THEN 'Echo + MRI'
          WHEN has_echo = 1 AND has_mri = 0 AND has_ecg = 1 THEN 'Echo + ECG'
          WHEN has_echo = 0 AND has_mri = 1 AND has_ecg = 1 THEN 'MRI + ECG'
          WHEN has_echo = 1 AND has_mri = 1 AND has_ecg = 1 THEN 'All Three'
          ELSE 'None'
        END as combination,
        COUNT(*) as count
      FROM patient_data
      GROUP BY combination
      ORDER BY count DESC
    `;

    return c.json({
      success: true,
      data: intersections
    });
  } catch (error) {
    console.error('Error fetching data intersections:', error);
    return c.json({ success: false, error: 'Failed to fetch data intersections' }, 500);
  }
});

export default analytics;
