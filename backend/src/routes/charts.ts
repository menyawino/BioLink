import { Hono } from 'hono';
import { sql } from '../db/connection.js';

const charts = new Hono();

// Get chart data based on configuration
charts.post('/generate', async (c) => {
  try {
    const { xAxis, yAxis, groupBy, chartType, filters } = await c.req.json();
    
    let data: any[] = [];
    
    // Age distribution
    if (xAxis === 'age' && !yAxis) {
      data = await sql`
        SELECT 
          CASE 
            WHEN age < 30 THEN '18-29'
            WHEN age BETWEEN 30 AND 39 THEN '30-39'
            WHEN age BETWEEN 40 AND 49 THEN '40-49'
            WHEN age BETWEEN 50 AND 59 THEN '50-59'
            WHEN age BETWEEN 60 AND 69 THEN '60-69'
            ELSE '70+'
          END as age_group,
          COUNT(*) as count,
          AVG(age) as mean,
          STDDEV(age) as sd
        FROM patients
        WHERE age IS NOT NULL
        GROUP BY age_group
        ORDER BY age_group
      `;
    }
    
    // Age vs Gender
    else if (xAxis === 'age' && groupBy === 'gender') {
      data = await sql`
        SELECT 
          CASE 
            WHEN age < 30 THEN '18-29'
            WHEN age BETWEEN 30 AND 39 THEN '30-39'
            WHEN age BETWEEN 40 AND 49 THEN '40-49'
            WHEN age BETWEEN 50 AND 59 THEN '50-59'
            WHEN age BETWEEN 60 AND 69 THEN '60-69'
            ELSE '70+'
          END as age_group,
          COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male,
          COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female
        FROM patients
        WHERE age IS NOT NULL
        GROUP BY age_group
        ORDER BY age_group
      `;
    }
    
    // BMI distribution
    else if (xAxis === 'bmi') {
      data = await sql`
        SELECT 
          CASE
            WHEN bmi < 18.5 THEN 'Underweight'
            WHEN bmi BETWEEN 18.5 AND 24.9 THEN 'Normal'
            WHEN bmi BETWEEN 25 AND 29.9 THEN 'Overweight'
            ELSE 'Obese'
          END as category,
          COUNT(*) as count,
          AVG(bmi) as mean,
          STDDEV(bmi) as sd
        FROM physical_examinations
        WHERE bmi IS NOT NULL
        GROUP BY category
      `;
    }
    
    // EF distribution
    else if (xAxis === 'ejectionFraction' || xAxis === 'ef') {
      data = await sql`
        SELECT 
          CASE 
            WHEN ef >= 55 THEN 'Normal (≥55%)'
            WHEN ef BETWEEN 40 AND 54 THEN 'Mild (40-54%)'
            WHEN ef BETWEEN 30 AND 39 THEN 'Moderate (30-39%)'
            ELSE 'Severe (<30%)'
          END as category,
          COUNT(*) as count,
          AVG(ef) as mean
        FROM echo_data
        WHERE ef IS NOT NULL
        GROUP BY category
      `;
    }
    
    // Age vs EF scatter
    else if (xAxis === 'age' && yAxis === 'ejectionFraction') {
      data = await sql`
        SELECT 
          p.age,
          ed.ef,
          p.gender
        FROM patients p
        JOIN echo_data ed ON p.id = ed.patient_id
        WHERE p.age IS NOT NULL AND ed.ef IS NOT NULL
        LIMIT 500
      `;
    }
    
    // BMI vs BP
    else if (xAxis === 'bmi' && yAxis === 'bloodPressure') {
      data = await sql`
        SELECT 
          pe.bmi,
          pe.systolic_bp,
          pe.diastolic_bp,
          p.gender
        FROM physical_examinations pe
        JOIN patients p ON pe.patient_id = p.id
        WHERE pe.bmi IS NOT NULL AND pe.systolic_bp IS NOT NULL
        LIMIT 500
      `;
    }
    
    // Data completeness over time
    else if (xAxis === 'timepoint' || xAxis === 'enrollment') {
      data = await sql`
        SELECT 
          TO_CHAR(p.enrollment_date, 'YYYY-MM') as timepoint,
          AVG(CASE WHEN pe.id IS NOT NULL THEN 100 ELSE 0 END) as physical_exam,
          AVG(CASE WHEN lr.id IS NOT NULL THEN 100 ELSE 0 END) as lab_results,
          AVG(CASE WHEN ecg.id IS NOT NULL THEN 100 ELSE 0 END) as ecg,
          AVG(CASE WHEN ed.id IS NOT NULL AND ed.missing_echo = FALSE THEN 100 ELSE 0 END) as echo,
          AVG(CASE WHEN md.id IS NOT NULL AND md.missing_mri = FALSE THEN 100 ELSE 0 END) as mri
        FROM patients p
        LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
        LEFT JOIN lab_results lr ON p.id = lr.patient_id
        LEFT JOIN ecg_data ecg ON p.id = ecg.patient_id
        LEFT JOIN echo_data ed ON p.id = ed.patient_id
        LEFT JOIN mri_data md ON p.id = md.patient_id
        WHERE p.enrollment_date IS NOT NULL
        GROUP BY timepoint
        ORDER BY timepoint
      `;
    }
    
    // Diagnosis/condition distribution (pie chart)
    else if (xAxis === 'diagnosis' || xAxis === 'conditions') {
      const conditions = await sql`
        SELECT 
          SUM(CASE WHEN high_blood_pressure THEN 1 ELSE 0 END) as hypertension,
          SUM(CASE WHEN diabetes_mellitus THEN 1 ELSE 0 END) as diabetes,
          SUM(CASE WHEN dyslipidemia THEN 1 ELSE 0 END) as dyslipidemia,
          SUM(CASE WHEN heart_attack_or_angina THEN 1 ELSE 0 END) as cad,
          SUM(CASE WHEN prior_heart_failure THEN 1 ELSE 0 END) as heart_failure
        FROM medical_history
      `;
      
      const c = conditions[0];
      data = [
        { name: 'Hypertension', value: parseInt(c.hypertension) || 0 },
        { name: 'Diabetes', value: parseInt(c.diabetes) || 0 },
        { name: 'Dyslipidemia', value: parseInt(c.dyslipidemia) || 0 },
        { name: 'CAD', value: parseInt(c.cad) || 0 },
        { name: 'Heart Failure', value: parseInt(c.heart_failure) || 0 }
      ];
    }
    
    // Default: return sample data
    else {
      data = await sql`
        SELECT 
          p.age,
          p.gender,
          pe.bmi,
          pe.systolic_bp,
          ed.ef
        FROM patients p
        LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
        LEFT JOIN echo_data ed ON p.id = ed.patient_id
        WHERE p.age IS NOT NULL
        LIMIT 100
      `;
    }

    return c.json({
      success: true,
      data,
      config: { xAxis, yAxis, groupBy, chartType }
    });
  } catch (error) {
    console.error('Error generating chart:', error);
    return c.json({ success: false, error: 'Failed to generate chart' }, 500);
  }
});

// Get available fields for chart building
charts.get('/fields', async (c) => {
  return c.json({
    success: true,
    data: {
      numeric: [
        { id: 'age', label: 'Age', table: 'patients' },
        { id: 'bmi', label: 'BMI', table: 'physical_examinations' },
        { id: 'systolic_bp', label: 'Systolic BP', table: 'physical_examinations' },
        { id: 'diastolic_bp', label: 'Diastolic BP', table: 'physical_examinations' },
        { id: 'heart_rate', label: 'Heart Rate', table: 'physical_examinations' },
        { id: 'hba1c', label: 'HbA1c', table: 'lab_results' },
        { id: 'troponin_i', label: 'Troponin I', table: 'lab_results' },
        { id: 'ef', label: 'Echo EF', table: 'echo_data' },
        { id: 'lv_ejection_fraction', label: 'MRI LV EF', table: 'mri_data' },
        { id: 'lv_mass', label: 'LV Mass', table: 'mri_data' },
        { id: 'smoking_years', label: 'Smoking Years', table: 'lifestyle_data' }
      ],
      categorical: [
        { id: 'gender', label: 'Gender', table: 'patients' },
        { id: 'nationality', label: 'Nationality', table: 'patients' },
        { id: 'marital_status', label: 'Marital Status', table: 'family_history' },
        { id: 'current_city_category', label: 'City Category', table: 'geographic_data' },
        { id: 'migration_pattern', label: 'Migration Pattern', table: 'geographic_data' },
        { id: 'ecg_conclusion', label: 'ECG Conclusion', table: 'ecg_data' },
        { id: 'rhythm', label: 'ECG Rhythm', table: 'ecg_data' }
      ],
      boolean: [
        { id: 'diabetes_mellitus', label: 'Diabetes', table: 'medical_history' },
        { id: 'high_blood_pressure', label: 'Hypertension', table: 'medical_history' },
        { id: 'dyslipidemia', label: 'Dyslipidemia', table: 'medical_history' },
        { id: 'current_smoker', label: 'Current Smoker', table: 'lifestyle_data' },
        { id: 'ever_smoked', label: 'Ever Smoked', table: 'lifestyle_data' }
      ]
    }
  });
});

// Get correlation data between two numeric fields
charts.get('/correlation', async (c) => {
  try {
    const field1 = c.req.query('field1') || 'age';
    const field2 = c.req.query('field2') || 'bmi';
    
    // Fetch all common numeric fields for correlation analysis
    const data = await sql`
      SELECT 
        p.age,
        p.gender,
        pe.bmi,
        pe.systolic_bp,
        pe.diastolic_bp,
        pe.heart_rate,
        lr.hba1c,
        lr.troponin_i,
        ed.ef,
        md.lv_ejection_fraction,
        md.lv_mass,
        ld.smoking_years
      FROM patients p
      LEFT JOIN physical_examinations pe ON p.id = pe.patient_id
      LEFT JOIN lab_results lr ON p.id = lr.patient_id
      LEFT JOIN echo_data ed ON p.id = ed.patient_id
      LEFT JOIN mri_data md ON p.id = md.patient_id
      LEFT JOIN lifestyle_data ld ON p.id = ld.patient_id
      WHERE p.age IS NOT NULL
      LIMIT 1000
    `;

    return c.json({ success: true, data });
  } catch (error) {
    console.error('Error fetching correlation data:', error);
    return c.json({ success: false, error: 'Failed to fetch correlation data' }, 500);
  }
});

export default charts;
