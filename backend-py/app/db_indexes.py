"""
Database index management for optimized queries.
"""

from sqlalchemy import text
from app.database import engine
import logging

logger = logging.getLogger(__name__)

# Index definitions for common query patterns
INDEXES = {
    # Patient lookup indexes
    "idx_patients_dna_id": "CREATE INDEX IF NOT EXISTS idx_patients_dna_id ON patients(dna_id)",
    "idx_patients_enrollment_date": "CREATE INDEX IF NOT EXISTS idx_patients_enrollment_date ON patients(enrollment_date)",
    # Demographic filters
    "idx_patients_age": "CREATE INDEX IF NOT EXISTS idx_patients_age ON patients(age)",
    "idx_patients_gender": "CREATE INDEX IF NOT EXISTS idx_patients_gender ON patients(gender)",
    "idx_patients_current_city": "CREATE INDEX IF NOT EXISTS idx_patients_current_city ON patients(current_city)",
    # Composite indexes for common filter combinations
    "idx_patients_demo": "CREATE INDEX IF NOT EXISTS idx_patients_demo ON patients(gender, age, current_city)",
    "idx_patients_enrollment_gender": "CREATE INDEX IF NOT EXISTS idx_patients_enrollment_gender ON patients(enrollment_date, gender)",
    # Medical condition indexes (if columns exist)
    "idx_patients_diabetes": "CREATE INDEX IF NOT EXISTS idx_patients_diabetes ON patients(diabetes_mellitus) WHERE diabetes_mellitus IS NOT NULL",
    "idx_patients_hypertension": "CREATE INDEX IF NOT EXISTS idx_patients_hypertension ON patients(high_blood_pressure) WHERE high_blood_pressure IS NOT NULL",
    # Full-text search index (PostgreSQL specific)
    "idx_patients_search": """
        CREATE INDEX IF NOT EXISTS idx_patients_search ON patients 
        USING gin(to_tsvector('english', coalesce(dna_id, '') || ' ' || 
        coalesce(current_city, '') || ' ' || 
        coalesce(cast(age as text), '')))
    """,
}

# Indexes for EHVOL view
EHVOL_INDEXES = {
    "idx_ehvol_dna_id": "CREATE INDEX IF NOT EXISTS idx_ehvol_dna_id ON EHVOL(dna_id)",
    "idx_ehvol_age": "CREATE INDEX IF NOT EXISTS idx_ehvol_age ON EHVOL(age)",
    "idx_ehvol_gender": "CREATE INDEX IF NOT EXISTS idx_ehvol_gender ON EHVOL(gender)",
    "idx_ehvol_city": "CREATE INDEX IF NOT EXISTS idx_ehvol_city ON EHVOL(current_city)",
}


def create_indexes():
    """Create all database indexes."""
    with engine.connect() as conn:
        # Create patients table indexes
        logger.info("Creating patients table indexes...")
        for name, sql in INDEXES.items():
            try:
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"✓ Created index: {name}")
            except Exception as e:
                logger.warning(f"✗ Failed to create index {name}: {e}")
                conn.rollback()

        # Create EHVOL view indexes
        logger.info("Creating EHVOL view indexes...")
        for name, sql in EHVOL_INDEXES.items():
            try:
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"✓ Created index: {name}")
            except Exception as e:
                logger.warning(f"✗ Failed to create index {name}: {e}")
                conn.rollback()

        logger.info("Index creation complete!")


def drop_indexes():
    """Drop all custom indexes (useful for migrations)."""
    all_indexes = {**INDEXES, **EHVOL_INDEXES}

    with engine.connect() as conn:
        logger.info("Dropping indexes...")
        for name in all_indexes.keys():
            try:
                conn.execute(text(f"DROP INDEX IF EXISTS {name}"))
                conn.commit()
                logger.info(f"✓ Dropped index: {name}")
            except Exception as e:
                logger.warning(f"✗ Failed to drop index {name}: {e}")
                conn.rollback()


def analyze_tables():
    """Run ANALYZE on tables for query planner optimization."""
    with engine.connect() as conn:
        logger.info("Analyzing tables...")
        try:
            conn.execute(text("ANALYZE patients"))
            conn.execute(text("ANALYZE EHVOL"))
            conn.commit()
            logger.info("✓ Table analysis complete")
        except Exception as e:
            logger.warning(f"✗ Table analysis failed: {e}")


def get_index_stats():
    """Get statistics about existing indexes."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename IN ('patients', 'EHVOL')
            ORDER BY tablename, indexname
        """))
        return result.fetchall()


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    print("Creating database indexes...")
    create_indexes()
    analyze_tables()

    print("\nCurrent indexes:")
    for row in get_index_stats():
        print(f"  - {row.indexname} on {row.tablename}")
