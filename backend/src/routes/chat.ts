import { Hono } from 'hono';
import postgres from 'postgres';
import { AzureOpenAI } from 'openai';
import { DefaultAzureCredential, getBearerTokenProvider } from '@azure/identity';
import '@azure/openai/types';

const chat = new Hono();

// Database connection
const sql = postgres(process.env.DATABASE_URL || 'postgres://postgres:postgres@localhost:5432/biolink');

// Configuration for Azure OpenAI
const AZURE_OPENAI_ENDPOINT = process.env.AZURE_OPENAI_ENDPOINT || '';
const AZURE_OPENAI_DEPLOYMENT = process.env.AZURE_OPENAI_DEPLOYMENT || 'gpt-4';
const AZURE_API_VERSION = process.env.AZURE_API_VERSION || '2024-10-21';

// Azure credential for authentication
const credential = new DefaultAzureCredential();
const scope = 'https://cognitiveservices.azure.com/.default';
const azureADTokenProvider = getBearerTokenProvider(credential, scope);

// Create Azure OpenAI client
let openaiClient: AzureOpenAI | null = null;
if (AZURE_OPENAI_ENDPOINT) {
  openaiClient = new AzureOpenAI({
    azureADTokenProvider,
    deployment: AZURE_OPENAI_DEPLOYMENT,
    apiVersion: AZURE_API_VERSION,
    endpoint: AZURE_OPENAI_ENDPOINT,
  });
}

// Tool/Function definitions for Azure OpenAI
const TOOLS = [
  {
    type: 'function',
    function: {
      name: 'search_patients',
      description: 'Search and filter patients in the registry. Returns patient list with demographics and data completeness.',
      parameters: {
        type: 'object',
        properties: {
          search: { type: 'string', description: 'Search by DNA ID, nationality, or city' },
          gender: { type: 'string', enum: ['Male', 'Female'], description: 'Filter by gender' },
          ageMin: { type: 'number', description: 'Minimum age filter' },
          ageMax: { type: 'number', description: 'Maximum age filter' },
          limit: { type: 'number', description: 'Number of results (max 100, default 20)' }
        }
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'get_patient_details',
      description: 'Get complete details for a specific patient including all clinical data.',
      parameters: {
        type: 'object',
        properties: {
          dnaId: { type: 'string', description: 'Patient DNA ID (e.g., EHV001)' }
        },
        required: ['dnaId']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'build_cohort',
      description: 'Build a patient cohort with filtering criteria. Returns matching patient count and list.',
      parameters: {
        type: 'object',
        properties: {
          ageMin: { type: 'number', description: 'Minimum age' },
          ageMax: { type: 'number', description: 'Maximum age' },
          gender: { type: 'string', enum: ['Male', 'Female'] },
          hasDiabetes: { type: 'boolean', description: 'Has diabetes' },
          hasHypertension: { type: 'boolean', description: 'Has hypertension' },
          hasSmoking: { type: 'boolean', description: 'Current smoker' },
          hasObesity: { type: 'boolean', description: 'BMI >= 30' },
          hasEcho: { type: 'boolean', description: 'Has echocardiography data' },
          hasMri: { type: 'boolean', description: 'Has MRI data' },
          limit: { type: 'number', description: 'Max results (default 100)' }
        }
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'get_registry_overview',
      description: 'Get high-level registry statistics: total patients, gender distribution, average age, data completeness.',
      parameters: { type: 'object', properties: {} }
    }
  },
  {
    type: 'function',
    function: {
      name: 'get_demographics_analysis',
      description: 'Analyze patient demographics: age/gender distribution, nationality breakdown, marital status.',
      parameters: { type: 'object', properties: {} }
    }
  },
  {
    type: 'function',
    function: {
      name: 'navigate_to_view',
      description: 'Navigate user to a specific section of the platform.',
      parameters: {
        type: 'object',
        properties: {
          view: { 
            type: 'string', 
            enum: ['registry', 'cohort', 'analytics', 'charts', 'dictionary'],
            description: 'Target view'
          }
        },
        required: ['view']
      }
    }
  }
];

const SYSTEM_PROMPT = `You are BioLink Assistant, an AI agent for the EHVol cardiovascular patient registry (669 patients).

**Your Role**: Help researchers and clinicians search patients, build cohorts, analyze data, and create visualizations.

**Available Tools**:
- search_patients: Find patients by criteria
- get_patient_details: View complete patient profile
- build_cohort: Create filtered patient cohorts
- get_registry_overview: Get statistics
- get_demographics_analysis: Analyze demographics
- navigate_to_view: Navigate the platform

**Guidelines**:
- Use tools proactively to answer questions with real data
- Provide specific numbers and insights from tool results
- Suggest logical next steps after actions
- Be concise and data-driven
- Always use tools when users ask about patients or statistics

Example: "How many patients have diabetes?" → Use build_cohort with hasDiabetes=true, then report the count.`;

interface ChatMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_calls?: any[];
  tool_call_id?: string;
  name?: string;
}

interface ChatRequest {
  message: string;
  history: ChatMessage[];
}

// Tool execution functions
async function executeTool(toolName: string, args: any): Promise<any> {
  console.log(`Executing tool: ${toolName}`, args);
  
  try {
    switch (toolName) {
      case 'search_patients':
        return await searchPatients(args);
      case 'get_patient_details':
        return await getPatientDetails(args.dnaId);
      case 'build_cohort':
        return await buildCohort(args);
      case 'get_registry_overview':
        return await getRegistryOverview();
      case 'get_demographics_analysis':
        return await getDemographicsAnalysis();
      case 'navigate_to_view':
        return { success: true, message: `Navigating to ${args.view} view`, action: 'navigate', view: args.view };
      default:
        return { error: `Unknown tool: ${toolName}` };
    }
  } catch (error) {
    console.error(`Tool execution error (${toolName}):`, error);
    return { error: error instanceof Error ? error.message : 'Tool execution failed' };
  }
}

async function searchPatients(params: any) {
  const { search, gender, ageMin, ageMax, limit = 20 } = params;
  
  let query = `
    SELECT p.dna_id, p.age, p.gender, p.nationality, 
           ROUND(p.data_completeness_score::numeric, 1) as data_completeness
    FROM patients p
    WHERE 1=1
  `;
  const values: any[] = [];
  let paramCount = 1;

  if (search) {
    query += ` AND (p.dna_id ILIKE $${paramCount} OR p.nationality ILIKE $${paramCount})`;
    values.push(`%${search}%`);
    paramCount++;
  }
  if (gender) {
    query += ` AND p.gender = $${paramCount}`;
    values.push(gender);
    paramCount++;
  }
  if (ageMin) {
    query += ` AND p.age >= $${paramCount}`;
    values.push(ageMin);
    paramCount++;
  }
  if (ageMax) {
    query += ` AND p.age <= $${paramCount}`;
    values.push(ageMax);
    paramCount++;
  }

  query += ` ORDER BY p.dna_id LIMIT $${paramCount}`;
  values.push(Math.min(limit, 100));

  const result = await sql.unsafe(query, values);
  return {
    success: true,
    count: result.length,
    patients: result
  };
}

async function getPatientDetails(dnaId: string) {
  const query = `
    SELECT p.*, 
           pe.bmi, pe.systolic_bp, pe.diastolic_bp, pe.heart_rate,
           lr.hba1c, lr.troponin_i,
           ed.ejection_fraction as echo_ef,
           md.lv_ejection_fraction as mri_ef
    FROM patients p
    LEFT JOIN physical_examinations pe ON p.patient_id = pe.patient_id
    LEFT JOIN lab_results lr ON p.patient_id = lr.patient_id
    LEFT JOIN echo_data ed ON p.patient_id = ed.patient_id
    LEFT JOIN mri_data md ON p.patient_id = md.patient_id
    WHERE p.dna_id = $1
  `;
  
  const result = await sql.unsafe(query, [dnaId]);
  if (result.length === 0) {
    return { success: false, error: `Patient ${dnaId} not found` };
  }
  
  return {
    success: true,
    patient: result[0]
  };
}

async function buildCohort(params: any) {
  const { ageMin, ageMax, gender, hasDiabetes, hasHypertension, hasSmoking, hasObesity, hasEcho, hasMri, limit = 100 } = params;
  
  let query = `
    SELECT p.dna_id, p.age, p.gender, p.nationality, p.data_completeness_score
    FROM patients p
    LEFT JOIN medical_history mh ON p.patient_id = mh.patient_id
    LEFT JOIN lifestyle_data ld ON p.patient_id = ld.patient_id
    LEFT JOIN physical_examinations pe ON p.patient_id = pe.patient_id
    LEFT JOIN echo_data ed ON p.patient_id = ed.patient_id
    LEFT JOIN mri_data md ON p.patient_id = md.patient_id
    WHERE 1=1
  `;
  const values: any[] = [];
  let paramCount = 1;

  if (ageMin) {
    query += ` AND p.age >= $${paramCount}`;
    values.push(ageMin);
    paramCount++;
  }
  if (ageMax) {
    query += ` AND p.age <= $${paramCount}`;
    values.push(ageMax);
    paramCount++;
  }
  if (gender) {
    query += ` AND p.gender = $${paramCount}`;
    values.push(gender);
    paramCount++;
  }
  if (hasDiabetes !== undefined) {
    query += ` AND mh.diabetes = $${paramCount}`;
    values.push(hasDiabetes);
    paramCount++;
  }
  if (hasHypertension !== undefined) {
    query += ` AND mh.hypertension = $${paramCount}`;
    values.push(hasHypertension);
    paramCount++;
  }
  if (hasSmoking !== undefined) {
    query += ` AND ld.current_smoker = $${paramCount}`;
    values.push(hasSmoking);
    paramCount++;
  }
  if (hasObesity !== undefined) {
    query += ` AND pe.bmi ${hasObesity ? '>=' : '<'} 30`;
  }
  if (hasEcho !== undefined) {
    query += ` AND ed.patient_id IS ${hasEcho ? 'NOT NULL' : 'NULL'}`;
  }
  if (hasMri !== undefined) {
    query += ` AND md.patient_id IS ${hasMri ? 'NOT NULL' : 'NULL'}`;
  }

  query += ` GROUP BY p.patient_id, p.dna_id, p.age, p.gender, p.nationality, p.data_completeness_score`;
  query += ` ORDER BY p.dna_id LIMIT $${paramCount}`;
  values.push(Math.min(limit, 100));

  const result = await sql.unsafe(query, values);
  return {
    success: true,
    count: result.length,
    cohort: result
  };
}

async function getRegistryOverview() {
  const query = `
    SELECT 
      COUNT(*) as total_patients,
      ROUND(AVG(age), 1) as avg_age,
      COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male_count,
      COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female_count,
      ROUND(AVG(data_completeness_score)::numeric, 1) as avg_completeness
    FROM patients
  `;
  
  const result = await sql.unsafe(query);
  return {
    success: true,
    overview: result[0]
  };
}

async function getDemographicsAnalysis() {
  const ageQuery = `
    SELECT 
      CASE 
        WHEN age < 30 THEN '<30'
        WHEN age < 40 THEN '30-39'
        WHEN age < 50 THEN '40-49'
        WHEN age < 60 THEN '50-59'
        WHEN age < 70 THEN '60-69'
        ELSE '70+'
      END as age_group,
      COUNT(CASE WHEN gender = 'Male' THEN 1 END) as male,
      COUNT(CASE WHEN gender = 'Female' THEN 1 END) as female
    FROM patients
    GROUP BY age_group
    ORDER BY age_group
  `;
  
  const nationalityQuery = `
    SELECT nationality, COUNT(*) as count
    FROM patients
    GROUP BY nationality
    ORDER BY count DESC
    LIMIT 10
  `;
  
  const [ageResult, nationalityResult] = await Promise.all([
    sql.unsafe(ageQuery),
    sql.unsafe(nationalityQuery)
  ]);
  
  return {
    success: true,
    demographics: {
      ageDistribution: ageResult,
      topNationalities: nationalityResult
    }
  };
}

// POST /api/chat - Send message to Azure OpenAI with function calling
chat.post('/', async (c) => {
  try {
    const body = await c.req.json<ChatRequest>();
    const { message, history = [] } = body;

    if (!message?.trim()) {
      return c.json({ success: false, error: 'Message is required' }, 400);
    }

    // Validate Azure configuration
    if (!openaiClient) {
      console.error('Azure OpenAI configuration missing');
      return c.json({
        success: true,
        data: {
          content: 'Azure OpenAI is not configured. Please set AZURE_OPENAI_ENDPOINT in backend/.env, then restart the server.',
          role: 'assistant',
          timestamp: new Date().toISOString(),
        }
      }, 200);
    }

    // Build messages array
    let messages: ChatMessage[] = [
      { role: 'system', content: SYSTEM_PROMPT },
      ...history,
      { role: 'user', content: message }
    ];
    
    let iterationCount = 0;
    const MAX_ITERATIONS = 5; // Prevent infinite loops
    
    // Function calling loop
    while (iterationCount < MAX_ITERATIONS) {
      iterationCount++;
      
      // Call Azure OpenAI using SDK
      const completion = await openaiClient.chat.completions.create({
        model: AZURE_OPENAI_DEPLOYMENT,
        messages: messages as any,
        tools: TOOLS as any,
        tool_choice: 'auto',
        temperature: 0.7,
        max_completion_tokens: 1500,
      });

      const choice = completion.choices?.[0];
      const assistantMessage = choice?.message;

      if (!assistantMessage) {
        return c.json({ 
          success: false, 
          error: 'No response from Azure OpenAI' 
        }, 500);
      }

      // Check if assistant wants to call tools
      if (assistantMessage.tool_calls && assistantMessage.tool_calls.length > 0) {
        // Add assistant message with tool calls to history
        messages.push({
          role: 'assistant',
          content: assistantMessage.content || '',
          tool_calls: assistantMessage.tool_calls as any
        });
        
        // Execute all tool calls
        for (const toolCall of assistantMessage.tool_calls) {
          const tc = toolCall as any;
          const functionName = tc.function.name;
          const functionArgs = JSON.parse(tc.function.arguments);
          
          console.log(`Tool call: ${functionName}`, functionArgs);
          
          // Execute the tool
          const toolResult = await executeTool(functionName, functionArgs);
          
          // Add tool result to messages
          messages.push({
            role: 'tool',
            tool_call_id: tc.id,
            name: functionName,
            content: JSON.stringify(toolResult)
          });
        }
        
        // Continue loop to get final response with tool results
        continue;
      }

      // No more tool calls, return final response
      return c.json({
        success: true,
        data: {
          content: assistantMessage.content || 'I apologize, but I could not generate a response.',
          role: 'assistant',
          timestamp: new Date().toISOString(),
        }
      });
    }

    // Max iterations reached
    return c.json({
      success: false,
      error: 'Maximum tool calling iterations reached'
    }, 500);

  } catch (error) {
    console.error('Error in chat endpoint:', error);
    return c.json({ 
      success: false, 
      error: 'Failed to process chat request',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, 500);
  }
});

// GET /api/chat/config - Get chat configuration status (for debugging)
chat.get('/config', async (c) => {
  return c.json({
    success: true,
    configured: !!openaiClient,
    endpoint: AZURE_OPENAI_ENDPOINT ? '***configured***' : 'not set',
    deployment: AZURE_OPENAI_DEPLOYMENT,
    apiVersion: AZURE_API_VERSION,
  });
});

export default chat;
