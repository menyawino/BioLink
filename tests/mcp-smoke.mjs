import assert from "node:assert/strict";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

const expectedTools = [
  "query_sql",
  "search_patients",
  "get_patient_details",
  "build_cohort",
  "registry_overview",
  "demographics",
  "enrollment_trends",
  "data_intersections",
  "chart_from_sql",
];

function extractText(result) {
  const textBlock = result?.content?.find((entry) => entry.type === "text");
  return textBlock?.text ?? "";
}

function parseToolPayload(result) {
  const text = extractText(result);

  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function callTool(client, name, args = {}) {
  const result = await client.callTool({ name, arguments: args });
  if (result.isError) {
    throw new Error(`Tool ${name} failed: ${extractText(result)}`);
  }

  return parseToolPayload(result);
}

async function main() {
  const transport = new StdioClientTransport({
    command: "node",
    args: ["mcp/server.mjs"],
    cwd: repoRoot,
    env: process.env,
    stderr: "inherit",
  });

  const client = new Client(
    {
      name: "biolink-mcp-smoke",
      version: "1.0.0",
    },
    {
      capabilities: {},
    }
  );

  try {
    await client.connect(transport);

    const toolList = await client.listTools({});
    const toolNames = toolList.tools.map((tool) => tool.name).sort();
    const missingTools = expectedTools.filter((tool) => !toolNames.includes(tool));
    assert.equal(missingTools.length, 0, `Missing tools: ${missingTools.join(", ")}`);

    const seedQuery = await callTool(client, "query_sql", {
      sql: `SELECT dna_id, age, gender,
                   COALESCE(current_city, nationality, current_city_category) AS region_hint
            FROM patients
            ORDER BY enrollment_date DESC NULLS LAST, dna_id
            LIMIT 1`,
    });
    assert.ok(Array.isArray(seedQuery?.rows), "query_sql did not return rows");
    assert.ok(seedQuery.rows.length > 0, "query_sql returned no patients");

    const samplePatient = seedQuery.rows[0];
    assert.ok(samplePatient.dna_id, "Sample patient is missing dna_id");

    const searchPatients = await callTool(client, "search_patients", {
      search: String(samplePatient.dna_id),
      limit: 5,
    });
    assert.ok(searchPatients.count >= 1, "search_patients returned no matches");

    const patientDetails = await callTool(client, "get_patient_details", {
      dna_id: String(samplePatient.dna_id),
    });
    assert.equal(String(patientDetails?.dna_id), String(samplePatient.dna_id), "get_patient_details returned the wrong patient");

    const cohort = await callTool(client, "build_cohort", {
      gender: samplePatient.gender ?? undefined,
      age_min: typeof samplePatient.age === "number" ? Math.max(0, samplePatient.age - 1) : undefined,
      age_max: typeof samplePatient.age === "number" ? samplePatient.age + 1 : undefined,
      has_imaging: false,
      has_labs: false,
      has_family_history: false,
      has_genomics: false,
      region: samplePatient.region_hint || undefined,
      limit: 5,
    });
    assert.equal(typeof cohort?.count, "number", "build_cohort did not return a count");
    assert.ok(Array.isArray(cohort?.rows), "build_cohort did not return rows");

    const registryOverview = await callTool(client, "registry_overview", {});
    assert.equal(typeof registryOverview?.total, "number", "registry_overview missing total");

    const demographics = await callTool(client, "demographics", {});
    assert.ok(Array.isArray(demographics?.ageGender), "demographics missing ageGender array");
    assert.ok(Array.isArray(demographics?.nationality), "demographics missing nationality array");

    const enrollmentTrends = await callTool(client, "enrollment_trends", {});
    assert.ok(Array.isArray(enrollmentTrends), "enrollment_trends did not return an array");

    const dataIntersections = await callTool(client, "data_intersections", {});
    assert.ok(Array.isArray(dataIntersections), "data_intersections did not return an array");

    const chart = await callTool(client, "chart_from_sql", {
      sql: `SELECT DATE_TRUNC('month', enrollment_date)::date AS month,
                   COUNT(*)::int AS enrolled
            FROM patients
            WHERE enrollment_date IS NOT NULL
            GROUP BY 1
            ORDER BY 1
            LIMIT 6`,
      mark: "bar",
      x: "month",
      y: "enrolled",
      x_type: "temporal",
      y_type: "quantitative",
      title: "Enrollment by month",
    });
    assert.ok(chart?.spec, "chart_from_sql did not return a Vega-Lite spec");
    assert.ok(Array.isArray(chart?.rows), "chart_from_sql did not return chart rows");

    console.log("MCP smoke test passed.");
    console.log(`Verified tools: ${toolNames.join(", ")}`);
  } finally {
    if (typeof client.close === "function") {
      await client.close();
    }
    await transport.close();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});