import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import pg from "pg";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.resolve(__dirname, "../backend-py/.env") });

const databaseUrl = process.env.DATABASE_URL;
if (!databaseUrl) {
  throw new Error("DATABASE_URL is not configured. Set it in backend-py/.env");
}

const pool = new pg.Pool({ connectionString: databaseUrl });

const server = new Server(
  {
    name: "biolink-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

function ensureSelect(sql) {
  const normalized = sql.trim().toLowerCase();
  return normalized.startsWith("select") || normalized.startsWith("with");
}

async function runQuery(sql, params = [], limit = 500) {
  if (!ensureSelect(sql)) {
    throw new Error("Only SELECT queries are allowed.");
  }

  const limitedSql = `${sql}\nLIMIT ${Number.isFinite(limit) ? Math.max(1, Math.min(limit, 2000)) : 500}`;
  const result = await pool.query(limitedSql, params);
  return result.rows;
}

const toolSchemas = {
  query_sql: z.object({
    sql: z.string().min(1),
    params: z.array(z.any()).optional(),
    limit: z.number().int().optional(),
  }),
  search_patients: z.object({
    search: z.string().optional(),
    gender: z.string().optional(),
    age_min: z.number().int().optional(),
    age_max: z.number().int().optional(),
    limit: z.number().int().optional(),
  }),
  get_patient_details: z.object({
    dna_id: z.string().min(1),
  }),
  build_cohort: z.object({
    age_min: z.number().int().optional(),
    age_max: z.number().int().optional(),
    gender: z.string().optional(),
    has_diabetes: z.boolean().optional(),
    has_hypertension: z.boolean().optional(),
    has_echo: z.boolean().optional(),
    has_mri: z.boolean().optional(),
    has_imaging: z.boolean().optional(),
    has_labs: z.boolean().optional(),
    has_genomics: z.boolean().optional(),
    has_family_history: z.boolean().optional(),
    region: z.string().optional(),
    limit: z.number().int().optional(),
  }),
  registry_overview: z.object({}).optional(),
  demographics: z.object({}).optional(),
  enrollment_trends: z.object({}).optional(),
  data_intersections: z.object({}).optional(),
  chart_from_sql: z.object({
    sql: z.string().min(1),
    limit: z.number().int().optional(),
    mark: z.enum(["line", "bar", "point", "area"]).optional(),
    x: z.string().min(1),
    y: z.string().min(1),
    color: z.string().optional(),
    x_type: z.enum(["quantitative", "temporal", "ordinal", "nominal"]).optional(),
    y_type: z.enum(["quantitative", "temporal", "ordinal", "nominal"]).optional(),
    title: z.string().optional(),
  }),
};

const tools = [
  {
    name: "query_sql",
    description: "Execute SQL queries against the database",
    inputSchema: {
      type: "object",
      properties: {
        sql: { type: "string" },
        params: { type: "array", items: {} },
        limit: { type: "integer" },
      },
      required: ["sql"],
    },
  },
  {
    name: "search_patients",
    description: "Search patient summary fields",
    inputSchema: {
      type: "object",
      properties: {
        search: { type: "string" },
        gender: { type: "string" },
        age_min: { type: "integer" },
        age_max: { type: "integer" },
        limit: { type: "integer" },
      },
    },
  },
  {
    name: "get_patient_details",
    description: "Get patient details by dna_id",
    inputSchema: {
      type: "object",
      properties: {
        dna_id: { type: "string" },
      },
      required: ["dna_id"],
    },
  },
  {
    name: "build_cohort",
    description: "Build a cohort with filters",
    inputSchema: {
      type: "object",
      properties: {
        age_min: { type: "integer" },
        age_max: { type: "integer" },
        gender: { type: "string" },
        has_diabetes: { type: "boolean" },
        has_hypertension: { type: "boolean" },
        has_echo: { type: "boolean" },
        has_mri: { type: "boolean" },
        has_imaging: { type: "boolean" },
        has_labs: { type: "boolean" },
        has_genomics: { type: "boolean" },
        has_family_history: { type: "boolean" },
        region: { type: "string" },
        limit: { type: "integer" },
      },
    },
  },
  {
    name: "registry_overview",
    description: "Get registry overview statistics",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "demographics",
    description: "Summarize demographics distributions",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "enrollment_trends",
    description: "Enrollment counts by month",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "data_intersections",
    description: "Echo/MRI overlap summary",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "chart_from_sql",
    description: "Generate a Vega-Lite chart from SQL results",
    inputSchema: {
      type: "object",
      properties: {
        sql: { type: "string" },
        limit: { type: "integer" },
        mark: { type: "string" },
        x: { type: "string" },
        y: { type: "string" },
        color: { type: "string" },
        x_type: { type: "string" },
        y_type: { type: "string" },
        title: { type: "string" },
      },
      required: ["sql", "x", "y"],
    },
  },
];

async function handleQuerySql(args) {
  const { sql, params, limit } = toolSchemas.query_sql.parse(args);
  const rows = await runQuery(sql, params || [], limit || 500);
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({ rows }, null, 2),
      },
    ],
  };
}

async function handleSearchPatients(args) {
  const { search, gender, age_min, age_max, limit } = toolSchemas.search_patients.parse(args);
  const clauses = [];
  const params = [];

  if (search) {
    params.push(`%${search}%`);
    clauses.push(`(dna_id ILIKE $${params.length} OR nationality ILIKE $${params.length} OR current_city_category ILIKE $${params.length})`);
  }
  if (gender) {
    params.push(gender.toLowerCase());
    clauses.push(`LOWER(gender) = $${params.length}`);
  }
  if (age_min !== undefined) {
    params.push(age_min);
    clauses.push(`age >= $${params.length}`);
  }
  if (age_max !== undefined) {
    params.push(age_max);
    clauses.push(`age <= $${params.length}`);
  }

  const where = clauses.length ? `WHERE ${clauses.join(" AND ")}` : "";
  const sql = `SELECT dna_id, age, gender, nationality, current_city_category, echo_ef, mri_ef
      FROM patient_summary
      ${where}
      ORDER BY dna_id`;

  const rows = await runQuery(sql, params, limit || 50);

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({ count: rows.length, rows }, null, 2),
      },
    ],
  };
}

async function handleGetPatientDetails(args) {
  const { dna_id } = toolSchemas.get_patient_details.parse(args);
  const rows = await runQuery(
    "SELECT * FROM patients WHERE dna_id = $1",
    [dna_id],
    1
  );
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(rows[0] || null, null, 2),
      },
    ],
  };
}

async function handleBuildCohort(args) {
  const { age_min, age_max, gender, has_diabetes, has_hypertension, has_echo, has_mri, limit } = toolSchemas.build_cohort.parse(args);
  const clauses = [];
  const params = [];

  if (age_min !== undefined) {
    params.push(age_min);
    clauses.push(`age >= $${params.length}`);
  }
  if (age_max !== undefined) {
    params.push(age_max);
    clauses.push(`age <= $${params.length}`);
  }
  if (gender) {
    params.push(gender.toLowerCase());
    clauses.push(`LOWER(gender) = $${params.length}`);
  }
  if (has_diabetes !== undefined) {
    clauses.push(`COALESCE(diabetes_mellitus, false) = ${has_diabetes}`);
  }
  if (has_hypertension !== undefined) {
    clauses.push(`COALESCE(high_blood_pressure, false) = ${has_hypertension}`);
  }
  if (has_echo !== undefined) {
    clauses.push(`(echo_ef IS NOT NULL) = ${has_echo}`);
  }
  if (has_mri !== undefined) {
    clauses.push(`(mri_ef IS NOT NULL) = ${has_mri}`);
  }

  if (has_imaging !== undefined) {
    clauses.push(`((mri_ef IS NOT NULL OR echo_ef IS NOT NULL) = ${has_imaging})`);
  }

  if (has_labs !== undefined) {
    clauses.push(`((hba1c IS NOT NULL OR troponin_i IS NOT NULL) = ${has_labs})`);
  }

  if (has_family_history !== undefined) {
    clauses.push(`((COALESCE(history_sudden_death, false) OR COALESCE(history_premature_cad, false)) = ${has_family_history})`);
  }

  if (has_genomics !== undefined) {
    if (has_genomics) {
      clauses.push(`EXISTS (SELECT 1 FROM patient_genomic_variants v WHERE v.dna_id = patients.dna_id)`);
    } else {
      clauses.push(`NOT EXISTS (SELECT 1 FROM patient_genomic_variants v WHERE v.dna_id = patients.dna_id)`);
    }
  }

  if (region) {
    params.push(`%${region.toLowerCase()}%`);
    clauses.push(`(LOWER(nationality) LIKE $${params.length} OR LOWER(current_city_category) LIKE $${params.length} OR LOWER(current_city) LIKE $${params.length})`);
  }

  const where = clauses.length ? `WHERE ${clauses.join(" AND ")}` : "";

  const sql = `SELECT dna_id, age, gender, nationality, echo_ef, mri_ef, diabetes_mellitus, high_blood_pressure
      FROM patients
      ${where}
      ORDER BY dna_id`;

  const rows = await runQuery(sql, params, limit || 200);

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({ count: rows.length, rows }, null, 2),
      },
    ],
  };
}

async function handleRegistryOverview() {
  const sql = `
    SELECT
      COUNT(*) AS total,
      COUNT(*) FILTER (WHERE LOWER(gender) IN ('male','m')) AS male,
      COUNT(*) FILTER (WHERE LOWER(gender) IN ('female','f')) AS female,
      AVG(age) AS avg_age,
      COUNT(*) FILTER (WHERE echo_ef IS NOT NULL) AS with_echo,
      COUNT(*) FILTER (WHERE mri_ef IS NOT NULL) AS with_mri
    FROM patients
  `;
  const rows = await runQuery(sql, [], 1);
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(rows[0] || {}, null, 2),
      },
    ],
  };
}

async function handleDemographics() {
  const ageGenderSql = `
    SELECT
      CASE
        WHEN age < 30 THEN '18-29'
        WHEN age < 40 THEN '30-39'
        WHEN age < 50 THEN '40-49'
        WHEN age < 60 THEN '50-59'
        WHEN age < 70 THEN '60-69'
        ELSE '70+'
      END AS age_group,
      COUNT(*) FILTER (WHERE LOWER(gender) IN ('male','m')) AS male,
      COUNT(*) FILTER (WHERE LOWER(gender) IN ('female','f')) AS female
    FROM patients
    WHERE age IS NOT NULL
    GROUP BY age_group
    ORDER BY age_group
  `;

  const nationalitySql = `
    SELECT nationality, COUNT(*) AS count
    FROM patients
    WHERE nationality IS NOT NULL AND nationality <> ''
    GROUP BY nationality
    ORDER BY count DESC
    LIMIT 10
  `;

  const ageGender = await runQuery(ageGenderSql, [], 50);
  const nationality = await runQuery(nationalitySql, [], 10);

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({ ageGender, nationality }, null, 2),
      },
    ],
  };
}

async function handleEnrollmentTrends() {
  const sql = `
    SELECT
      TO_CHAR(DATE_TRUNC('month', enrollment_date), 'YYYY-MM') AS month,
      COUNT(*) AS enrolled
    FROM patients
    WHERE enrollment_date IS NOT NULL
    GROUP BY month
    ORDER BY month
  `;
  const rows = await runQuery(sql, [], 200);
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(rows, null, 2),
      },
    ],
  };
}

async function handleDataIntersections() {
  const sql = `
    SELECT
      CASE
        WHEN echo_ef IS NOT NULL AND mri_ef IS NOT NULL THEN 'Echo+MRI'
        WHEN echo_ef IS NOT NULL AND mri_ef IS NULL THEN 'Echo only'
        WHEN echo_ef IS NULL AND mri_ef IS NOT NULL THEN 'MRI only'
        ELSE 'No Echo/MRI'
      END AS combination,
      COUNT(*) AS count
    FROM patients
    GROUP BY combination
    ORDER BY count DESC
  `;
  const rows = await runQuery(sql, [], 10);
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(rows, null, 2),
      },
    ],
  };
}

async function handleChartFromSql(args) {
  const { sql, limit, mark, x, y, color, x_type, y_type, title } = toolSchemas.chart_from_sql.parse(args);
  const rows = await runQuery(sql, [], limit || 500);
  const spec = {
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    description: "Generated by biolink-mcp",
    title: title || "Chart",
    data: { values: rows },
    mark: mark || "line",
    encoding: {
      x: { field: x, type: x_type || "temporal" },
      y: { field: y, type: y_type || "quantitative" },
      ...(color ? { color: { field: color, type: "nominal" } } : {}),
    },
  };

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({ spec, rows }, null, 2),
      },
    ],
  };
}

const toolHandlers = {
  query_sql: handleQuerySql,
  search_patients: handleSearchPatients,
  get_patient_details: handleGetPatientDetails,
  build_cohort: handleBuildCohort,
  registry_overview: handleRegistryOverview,
  demographics: handleDemographics,
  enrollment_trends: handleEnrollmentTrends,
  data_intersections: handleDataIntersections,
  chart_from_sql: handleChartFromSql,
};

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const name = request.params?.name;
  const args = request.params?.arguments || {};
  const handler = toolHandlers[name];

  if (!handler) {
    throw new Error(`Unknown tool: ${name}`);
  }

  return handler(args);
});

const transport = new StdioServerTransport();
await server.connect(transport);
