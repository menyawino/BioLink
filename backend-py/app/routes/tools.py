from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from app.database import engine
import sqlalchemy as sa

logger = logging.getLogger(__name__)

router = APIRouter()

class ToolRequest(BaseModel):
    tool: str
    arguments: dict

@router.post("/")
async def call_tool(request: ToolRequest):
    """Execute an MCP tool via database queries"""
    try:
        if request.tool == "registry_overview":
            return await registry_overview()
        elif request.tool == "query_sql":
            return await query_sql(request.arguments)
        elif request.tool == "search_patients":
            return await search_patients(request.arguments)
        elif request.tool == "build_cohort":
            return await build_cohort(request.arguments)
        elif request.tool == "chart_from_sql":
            return await chart_from_sql(request.arguments)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

async def registry_overview():
    """Get overview statistics of the patient registry"""
    query = """
    SELECT
      COUNT(*) AS total,
      COUNT(*) FILTER (WHERE LOWER(gender) IN ('male','m')) AS male,
      COUNT(*) FILTER (WHERE LOWER(gender) IN ('female','f')) AS female,
      ROUND(AVG(age), 1) AS avg_age,
      COUNT(*) FILTER (WHERE echo_ef IS NOT NULL) AS with_echo,
      COUNT(*) FILTER (WHERE mri_ef IS NOT NULL) AS with_mri
    FROM patients
    """
    
    with engine.connect() as conn:
        result = conn.execute(sa.text(query))
        row = result.fetchone()
        
    return {
        "total": row[0],
        "male": row[1], 
        "female": row[2],
        "avg_age": float(row[3]) if row[3] else None,
        "with_echo": row[4],
        "with_mri": row[5]
    }

async def query_sql(args: dict):
    """Execute SQL queries against the database"""
    sql = args.get("sql", "")
    limit = args.get("limit", 500)
    
    # Basic security check
    if not sql.strip().upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    
    # Add limit if not present
    if "LIMIT" not in sql.upper():
        sql = f"{sql} LIMIT {limit}"
    
    with engine.connect() as conn:
        result = conn.execute(sa.text(sql))
        rows = result.fetchall()
        columns = result.keys()
        
    return {
        "rows": [dict(zip(columns, row)) for row in rows],
        "count": len(rows)
    }

async def search_patients(args: dict):
    """Search for patients with specific criteria"""
    conditions = []
    params = {}
    
    if "search" in args and args["search"]:
        search_term = f"%{args['search']}%"
        conditions.append("(LOWER(name) LIKE :search OR CAST(dna_id AS TEXT) LIKE :search)")
        params["search"] = search_term.lower()
    
    if "gender" in args and args["gender"]:
        conditions.append("LOWER(gender) = :gender")
        params["gender"] = args["gender"].lower()
    
    if "age_min" in args and args["age_min"] is not None:
        conditions.append("age >= :age_min")
        params["age_min"] = args["age_min"]
    
    if "age_max" in args and args["age_max"] is not None:
        conditions.append("age <= :age_max")
        params["age_max"] = args["age_max"]
    
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    limit = args.get("limit", 50)
    
    query = f"""
    SELECT dna_id, name, age, gender, enrollment_date
    FROM patients 
    WHERE {where_clause}
    ORDER BY enrollment_date DESC
    LIMIT {limit}
    """
    
    with engine.connect() as conn:
        result = conn.execute(sa.text(query), params)
        rows = result.fetchall()
        columns = result.keys()
    
    return {
        "rows": [dict(zip(columns, row)) for row in rows],
        "count": len(rows)
    }

async def build_cohort(args: dict):
    """Build a patient cohort with specific criteria"""
    conditions = []
    params = {}
    
    if args.get("age_min") is not None:
        conditions.append("age >= :age_min")
        params["age_min"] = args["age_min"]
    
    if args.get("age_max") is not None:
        conditions.append("age <= :age_max")
        params["age_max"] = args["age_max"]
    
    if args.get("gender"):
        conditions.append("LOWER(gender) = :gender")
        params["gender"] = args["gender"].lower()
    
    if args.get("has_diabetes"):
        conditions.append("diabetes = :has_diabetes")
        params["has_diabetes"] = args["has_diabetes"]
    
    if args.get("has_hypertension"):
        conditions.append("hypertension = :has_hypertension")
        params["has_hypertension"] = args["has_hypertension"]
    
    if args.get("has_echo"):
        conditions.append("echo_ef IS NOT NULL")
    
    if args.get("has_mri"):
        conditions.append("mri_ef IS NOT NULL")
    
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    limit = args.get("limit", 100)
    
    query = f"""
    SELECT 
      dna_id, name, age, gender, 
      diabetes, hypertension, 
      echo_ef, mri_ef,
      enrollment_date
    FROM patients 
    WHERE {where_clause}
    ORDER BY enrollment_date DESC
    LIMIT {limit}
    """
    
    with engine.connect() as conn:
        result = conn.execute(sa.text(query), params)
        rows = result.fetchall()
        columns = result.keys()
    
    return {
        "rows": [dict(zip(columns, row)) for row in rows],
        "count": len(rows)
    }

async def chart_from_sql(args: dict):
    """Create charts from SQL query results"""
    sql = args.get("sql", "")
    limit = args.get("limit", 500)
    
    if not sql.strip().upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    
    if "LIMIT" not in sql.upper():
        sql = f"{sql} LIMIT {limit}"
    
    with engine.connect() as conn:
        result = conn.execute(sa.text(sql))
        rows = result.fetchall()
        columns = result.keys()
    
    data = [dict(zip(columns, row)) for row in rows]
    
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "Generated chart",
        "title": args.get("title", "Chart"),
        "data": {"values": data},
        "mark": args.get("mark", "bar"),
        "encoding": {
            "x": {
                "field": args.get("x"),
                "type": args.get("x_type", "ordinal")
            },
            "y": {
                "field": args.get("y"), 
                "type": args.get("y_type", "quantitative")
            }
        }
    }
    
    if args.get("color"):
        spec.encoding.color = {
            "field": args["color"],
            "type": "nominal"
        }
    
    return {
        "spec": spec,
        "rows": data,
        "count": len(data)
    }