#!/usr/bin/env python3
"""
BioLink ETL Verification Script
=================================
Verifies that BHS and EHVol data has been ingested correctly into PostgreSQL.

Usage:
    python3 nifi/scripts/verify_ingestion.py [--host localhost] [--port 5432]
"""
import argparse
import sys

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("Installing psycopg2-binary...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "-q"])
    import psycopg2
    import psycopg2.extras


def verify(host="localhost", port=5432, db="biolink", user="biolink", password="biolink_secret"):
    """Run verification queries."""
    conn = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=password)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("=" * 70)
    print("  BioLink ETL Ingestion Verification")
    print("=" * 70)

    # 1. Table existence
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('bhs_participants', 'ehvol_participants', 'etl_run_history', 'city_homogenization_audit')
        ORDER BY table_name
    """)
    tables = [r["table_name"] for r in cur.fetchall()]
    print(f"\n[Tables] Found: {', '.join(tables)}")

    # 2. Row counts
    for table in ["bhs_participants", "ehvol_participants"]:
        if table in tables:
            cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            cnt = cur.fetchone()["cnt"]
            print(f"  {table}: {cnt:,} rows")
        else:
            print(f"  {table}: TABLE MISSING")

    # 3. Unified view
    try:
        cur.execute("SELECT COUNT(*) as cnt FROM unified_participants")
        cnt = cur.fetchone()["cnt"]
        print(f"  unified_participants (view): {cnt:,} rows")
    except Exception as e:
        print(f"  unified_participants (view): ERROR - {e}")
        conn.rollback()

    # 4. Gender distribution
    print("\n[Quality] Gender distribution:")
    for table in ["bhs_participants", "ehvol_participants"]:
        if table not in tables:
            continue
        cur.execute(f"SELECT gender, COUNT(*) as cnt FROM {table} GROUP BY gender ORDER BY cnt DESC")
        rows = cur.fetchall()
        print(f"  {table}:")
        for r in rows:
            print(f"    {r['gender'] or 'NULL'}: {r['cnt']:,}")

    # 5. City distribution (top 10)
    print("\n[Quality] Top 10 cities (unified):")
    try:
        cur.execute("""
            SELECT current_city, COUNT(*) as cnt
            FROM unified_participants
            WHERE current_city IS NOT NULL
            GROUP BY current_city
            ORDER BY cnt DESC
            LIMIT 10
        """)
        for r in cur.fetchall():
            print(f"  {r['current_city']}: {r['cnt']:,}")
    except Exception as e:
        print(f"  ERROR: {e}")
        conn.rollback()

    # 6. Quality score distribution
    print("\n[Quality] Quality score distribution:")
    for table in ["bhs_participants", "ehvol_participants"]:
        if table not in tables:
            continue
        cur.execute(f"""
            SELECT
                ROUND(AVG(data_quality_score)::numeric, 2) as avg_score,
                ROUND(MIN(data_quality_score)::numeric, 2) as min_score,
                ROUND(MAX(data_quality_score)::numeric, 2) as max_score,
                COUNT(*) FILTER (WHERE data_quality_score >= 0.8) as high_quality,
                COUNT(*) FILTER (WHERE data_quality_score >= 0.5 AND data_quality_score < 0.8) as medium_quality,
                COUNT(*) FILTER (WHERE data_quality_score < 0.5) as low_quality
            FROM {table}
        """)
        r = cur.fetchone()
        print(f"  {table}:")
        print(f"    Score: avg={r['avg_score']}, min={r['min_score']}, max={r['max_score']}")
        print(f"    High (>=0.8): {r['high_quality']}, Medium (0.5-0.8): {r['medium_quality']}, Low (<0.5): {r['low_quality']}")

    # 7. Null field analysis
    print("\n[Quality] Non-null field coverage:")
    key_fields = [
        "participant_id", "age", "gender", "current_city",
        "height_cm", "weight_kg", "bmi", "systolic_bp", "diastolic_bp",
        "hba1c", "has_diabetes", "is_smoker",
    ]
    for table in ["bhs_participants", "ehvol_participants"]:
        if table not in tables:
            continue
        cur.execute(f"SELECT COUNT(*) as total FROM {table}")
        total = cur.fetchone()["total"]
        if total == 0:
            print(f"  {table}: EMPTY")
            continue
        print(f"  {table} ({total} rows):")
        for field in key_fields:
            try:
                cur.execute(f"SELECT COUNT({field}) as cnt FROM {table}")
                cnt = cur.fetchone()["cnt"]
                pct = (cnt / total * 100) if total > 0 else 0
                print(f"    {field}: {cnt}/{total} ({pct:.0f}%)")
            except Exception:
                conn.rollback()

    # 8. Index verification
    print("\n[Indexes] Checking indexes:")
    cur.execute("""
        SELECT indexname, tablename
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename IN ('bhs_participants', 'ehvol_participants')
        ORDER BY tablename, indexname
    """)
    for r in cur.fetchall():
        print(f"  {r['tablename']}: {r['indexname']}")

    # 9. Sample records
    print("\n[Sample] First record from each table:")
    for table in ["bhs_participants", "ehvol_participants"]:
        if table not in tables:
            continue
        cur.execute(f"""
            SELECT participant_id, source_dataset, age, gender, current_city,
                   bmi, systolic_bp, diastolic_bp, data_quality_score
            FROM {table} LIMIT 1
        """)
        r = cur.fetchone()
        if r:
            print(f"  {table}:")
            for k, v in r.items():
                print(f"    {k}: {v}")

    cur.close()
    conn.close()
    print("\n" + "=" * 70)
    print("  Verification complete!")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5432)
    args = parser.parse_args()
    verify(host=args.host, port=args.port)
