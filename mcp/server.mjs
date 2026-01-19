import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
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

server.tool(
  "query_sql",
  {
    sql: z.string().min(1),
    params: z.array(z.any()).optional(),
    limit: z.number().int().optional(),
  },
  async ({ sql, params, limit }) => {
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
);

server.tool(
  "search_patients",
  {
    search: z.string().optional(),
    gender: z.string().optional(),
    age_min: z.number().int().optional(),
    age_max: z.number().int().optional(),
    limit: z.number().int().optional(),
  },
  async ({ search, gender, age_min, age_max, limit }) => {
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
);

server.tool(
  "get_patient_details",
  {
    dna_id: z.string().min(1),
  },
  async ({ dna_id }) => {
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
);

server.tool(
  "build_cohort",
  {
    age_min: z.number().int().optional(),
    age_max: z.number().int().optional(),
    gender: z.string().optional(),
    has_diabetes: z.boolean().optional(),
    has_hypertension: z.boolean().optional(),
    has_echo: z.boolean().optional(),
    has_mri: z.boolean().optional(),
    limit: z.number().int().optional(),
  },
  async ({ age_min, age_max, gender, has_diabetes, has_hypertension, has_echo, has_mri, limit }) => {
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
);

server.tool("registry_overview", {}, async () => {
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
});

server.tool("demographics", {}, async () => {
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
});

server.tool("enrollment_trends", {}, async () => {
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
});

server.tool("data_intersections", {}, async () => {
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
});

server.tool(
  "chart_from_sql",
  {
    sql: z.string().min(1),
    limit: z.number().int().optional(),
    mark: z.enum(["line", "bar", "point", "area"]).optional(),
    x: z.string().min(1),
    y: z.string().min(1),
    color: z.string().optional(),
    x_type: z.enum(["quantitative", "temporal", "ordinal", "nominal"]).optional(),
    y_type: z.enum(["quantitative", "temporal", "ordinal", "nominal"]).optional(),
    title: z.string().optional(),
  },
  async ({ sql, limit, mark, x, y, color, x_type, y_type, title }) => {
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
);

const transport = new StdioServerTransport();
await server.connect(transport);
