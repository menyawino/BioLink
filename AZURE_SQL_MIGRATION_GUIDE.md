# Azure SQL Migration Guide for BioLink

## Overview
This guide consolidates your EHVol data from Foundry IQ knowledge base into Azure SQL as a single source of truth for your agent.

---

## Step 1: Apply Schema to Azure SQL

**Portal Steps:**
1. Azure Portal → `biolink` database → **Query editor (preview)**
2. Sign in with your Entra admin account
3. Copy the entire contents of `backend/init/01_schema_azure_sql.sql`
4. Paste into Query editor and click **Run**
5. Verify: You should see 13 tables and 5 views created

**Key Changes from PostgreSQL:**
- `SERIAL` → `INT IDENTITY(1,1)`
- `BOOLEAN` → `BIT` (1/0)
- `TEXT` → `NVARCHAR(MAX)`
- `TIMESTAMP` → `DATETIME2`
- Views use `GO` batch separators and explicit GROUP BY

---

## Step 2: Load CSV Data into Azure SQL

### Option A: Azure Data Factory (Recommended for Portal)

**Setup:**
1. Azure Portal → Create **Data Factory** resource (same region as SQL)
2. Open Data Factory Studio → Author → New Pipeline
3. Add **Copy Data** activity:
   - **Source:** HTTP (if CSV is in GitHub/blob) or Upload to Blob Storage first
   - **Sink:** Azure SQL Database (`biolink`)
   - **Mapping:** Auto-map CSV columns to table columns

**CSV Location:**
- Your CSV: `db/100925_Cleaned_EHVol_Data_STANDARDIZED.csv`
- Upload to Azure Blob Storage first, then reference in ADF

**Table Mapping:**
- The CSV is denormalized; you'll need to split into the 13 tables
- Primary table: `patients`
- Related tables: `lifestyle_data`, `medical_history`, `physical_examinations`, etc.

### Option B: BCP (Command Line - Faster for Testing)

**If you want to try locally first:**
```bash
# Install Azure Data Studio or SQL Server tools
# Example for macOS (requires Docker or native tools)

# Upload CSV to blob, then use Azure Data Studio's Import wizard:
# 1. Open Azure Data Studio
# 2. Connect to biolink (Entra auth)
# 3. Right-click database → Import Wizard
# 4. Select CSV, map columns to tables
```

### Option C: Python Script (Automated)

Create a script to parse the CSV and insert rows:

```python
import pandas as pd
import pyodbc
from azure.identity import DefaultAzureCredential

# Read CSV
df = pd.read_csv('db/100925_Cleaned_EHVol_Data_STANDARDIZED.csv')

# Connect with Entra auth
connection_string = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tcp:<server>.database.windows.net,1433;"
    "Database=biolink;"
    "Authentication=ActiveDirectoryInteractive;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)
conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

# Insert patients (example)
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO patients (dna_id, date_of_birth, age, gender, nationality, ...)
        VALUES (?, ?, ?, ?, ?, ...)
    """, row['DNA_ID'], row['DOB'], row['Age'], row['Gender'], row['Nationality'], ...)

conn.commit()
conn.close()
```

**Note:** The CSV structure needs to be analyzed to map to the normalized schema. Let me know if you want me to create a full import script.

---

## Step 3: Configure Entra ID Authentication

**Set Entra Admin:**
1. Azure Portal → SQL server → **Microsoft Entra ID**
2. Click **Set admin** → select your account or a service principal
3. Save

**Add MCP Service Principal:**
1. In Foundry, find your agent's **Managed Identity** or **Service Principal name**
2. In Azure Portal → `biolink` database → Query editor
3. Run:
```sql
-- Replace <AGENT_NAME> with your Foundry agent's service principal display name
CREATE USER [<AGENT_NAME>] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [<AGENT_NAME>];
ALTER ROLE db_datawriter ADD MEMBER [<AGENT_NAME>];
```

**Verify:**
```sql
SELECT name, type_desc FROM sys.database_principals WHERE name = '<AGENT_NAME>';
```

---

## Step 4: Add SQL MCP Tool in Foundry

**Foundry Portal Steps:**
1. Open your Foundry project
2. Go to **Tools** (or **Agents → Tools**)
3. Click **Add MCP Tool** → **Azure SQL Database**
4. Configure:
   - **Name:** `biolink-sql`
   - **Server:** `<yourserver>.database.windows.net`
   - **Database:** `biolink`
   - **Authentication:** Microsoft Entra ID (Managed Identity)
   - **Port:** 1433 (default)
5. Test connection → Save
6. Copy the **MCP Tool Endpoint** (you'll use this in agent config)

---

## Step 5: Connect Agent to SQL (Remove Foundry IQ)

**Update Agent Configuration:**
1. Open your agent in Foundry
2. Go to **Tools/Data Sources**
3. **Remove** or disable the Foundry IQ knowledge base (CSV source)
4. **Add** the `biolink-sql` MCP tool
5. Update agent instructions/system prompt:
   - "Query the biolink SQL database for patient data using the biolink-sql tool"
   - Provide table/column names or schema summary in agent instructions
6. Save and deploy

---

## Step 6: Test Agent Queries

**Sample Test Queries via Agent:**
- "How many patients are in the database?"
  - Expected SQL: `SELECT COUNT(*) FROM patients;`
- "Show me patients with diabetes and high blood pressure"
  - Expected SQL: `SELECT p.dna_id, p.age, p.gender FROM patients p JOIN medical_history mh ON p.id = mh.patient_id WHERE mh.diabetes_mellitus = 1 AND mh.high_blood_pressure = 1;`
- "What's the average BMI by age group?"
  - Expected SQL: `SELECT age_group, AVG(bmi) FROM demographics_analytics JOIN physical_examinations ... GROUP BY age_group;`

**Verify:**
- Agent generates correct SQL
- Data returns successfully
- No errors about missing tables/columns

---

## Architecture Summary

**Before:**
- CSV in Foundry IQ → Limited structured queries, dual source problem

**After:**
- CSV data → Azure SQL `biolink` database
- Agent → SQL MCP tool (Entra auth) → Azure SQL
- Single source of truth, full SQL query capability

---

## Next Steps

1. ✅ Apply schema (`01_schema_azure_sql.sql`)
2. ⏳ Load CSV data (choose ADF, BCP, or Python script)
3. ⏳ Add Entra user for MCP agent
4. ⏳ Configure SQL MCP tool in Foundry
5. ⏳ Update agent to use SQL tool, remove IQ source
6. ⏳ Test queries

---

## Troubleshooting

**Connection fails:**
- Verify firewall rules (Portal → SQL server → Networking)
- Confirm Entra admin is set
- Check service principal has db_datareader/db_datawriter roles

**Schema errors:**
- Ensure you ran the full `01_schema_azure_sql.sql` script
- Check for batch errors (GO statements)
- Views must be created after tables

**CSV import fails:**
- Verify column names match table schema
- Handle NULL values and data type conversions
- Consider staging table first, then insert into normalized tables

**Agent can't query:**
- Verify MCP tool endpoint is correct
- Check agent has the SQL tool added in configuration
- Review agent system prompt includes table/schema info

---

## Cost Optimization

- Use **Serverless** compute tier for dev/test (auto-pause)
- Set vCore min/max (e.g., 0.5–2 vCores)
- Auto-pause delay: 60 minutes
- For production: evaluate Provisioned vs Serverless based on usage patterns

---

## Security Best Practices

- ✅ Use Entra ID authentication (no passwords)
- ✅ Least privilege: db_datareader + db_datawriter only
- ✅ Enable Private Link/VNet for production
- ✅ Transparent Data Encryption (enabled by default)
- ✅ Regular backups (automated)
- ⚠️ Disable public network access for production
- ⚠️ Use separate dev/test databases

---

For questions or issues, refer to:
- Azure SQL Flexible Server docs: https://learn.microsoft.com/azure/azure-sql/
- Foundry MCP tools: https://learn.microsoft.com/azure/ai-studio/
