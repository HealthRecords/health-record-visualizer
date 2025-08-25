#!/usr/bin/env python3
"""
Preprocessor for CDA XML files to extract observations into SQLite database.

Handles the 700MB export_cda.xml file by parsing it in streaming fashion
and storing observations in a SQLite database for efficient querying.
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Optional, Generator
import time

from xml_reader import get_test_results, trim, find
import xml.etree.ElementTree as ET
import unicodedata
from health_lib import Observation, ValueQuantity
from datetime import datetime


def create_database(db_path: Path) -> sqlite3.Connection:
    """
    Create SQLite database with schema for CDA observations.
    """
    conn = sqlite3.connect(db_path)
    
    # Create observations table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cda_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            date TEXT NOT NULL,
            source_name TEXT,
            file_source TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for efficient querying
    conn.execute("CREATE INDEX IF NOT EXISTS idx_category_name ON cda_observations (category, name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON cda_observations (date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON cda_observations (source_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON cda_observations (name)")
    
    conn.commit()
    return conn


def get_all_observations(file_name: str) -> Generator[Observation, None, None]:
    """
    Get ALL observations from CDA XML file (modified version of xml_reader.get_test_results).
    """
    element_stack: list[str] = []
    unit = None
    value = None
    dt_string = None
    source_name = None
    ob: Optional[Observation] = None
    
    for index, i in enumerate(ET.iterparse(file_name, events=("start", "end"))):
        event, element = i
        tag: str = unicodedata.normalize("NFKD", trim(element.tag))
        
        if event == "start":
            element_stack.append(tag)
            if find(element_stack, ["component", "observation", "code"]):
                dn = element.attrib.get('displayName')
                if dn:  # Create observation for ANY display name
                    ob = Observation(name=dn)
                    
        elif event == "end":
            if find(element_stack, ["component", "observation", "text", "sourceName"]):
                if element.text is None:
                    source_name = "Unknown"
                else:
                    source_name = unicodedata.normalize("NFKD", element.text)

            if find(element_stack, ["component", "observation", "text", "unit"]):
                unit = element.text

            if find(element_stack, ["component", "observation", "text", "value"]):
                try:
                    value = float(element.text)
                except (ValueError, TypeError):
                    value = None

            if find(element_stack, ["component", "observation", "effectiveTime", "low"]):
                timestamp = element.attrib.get('value')
                if timestamp:
                    try:
                        dt_obj = datetime.strptime(timestamp, '%Y%m%d%H%M%S%z')
                        dt_string = datetime.strftime(dt_obj, '%Y-%m-%dT%H:%M:%SZ')
                    except ValueError:
                        dt_string = None

            if find(element_stack, ["component", "observation"]):
                if ob is not None and value is not None and unit is not None and dt_string is not None and source_name is not None:
                    vq = ValueQuantity(value, unit, ob.name)
                    ob.data = [vq]
                    ob.filename = file_name
                    ob.date = dt_string
                    ob.source_name = source_name
                    yield ob
                    
                # Reset for next observation
                ob = None
                value = None
                unit = None
                dt_string = None
                source_name = None

            element_stack.pop()


def categorize_observation(name: str) -> str:
    """
    Categorize observation based on name.
    """
    name_lower = name.lower()
    
    if any(term in name_lower for term in ['heart rate', 'pulse']):
        return 'Vital Signs'
    elif any(term in name_lower for term in ['oxygen', 'spo2', 'saturation']):
        return 'Vital Signs' 
    elif any(term in name_lower for term in ['respiratory', 'breathing', 'breath']):
        return 'Vital Signs'
    elif any(term in name_lower for term in ['temperature', 'temp']):
        return 'Vital Signs'
    elif any(term in name_lower for term in ['blood pressure', 'systolic', 'diastolic']):
        return 'Vital Signs'
    elif any(term in name_lower for term in ['glucose', 'sugar']):
        return 'Laboratory'
    elif any(term in name_lower for term in ['weight', 'mass']):
        return 'Biometrics'
    elif any(term in name_lower for term in ['height', 'stature']):
        return 'Biometrics'
    else:
        return 'Other'


def process_cda_file(cda_file: Path, db_path: Path, batch_size: int = 1000) -> None:
    """
    Process CDA XML file and populate SQLite database.
    """
    print(f"Creating database: {db_path}")
    conn = create_database(db_path)
    
    print(f"Processing CDA file: {cda_file}")
    print("This may take several minutes for large files...")
    
    start_time = time.time()
    batch = []
    total_count = 0
    
    try:
        # Process all observations from CDA file
        for observation in get_all_observations(str(cda_file)):
            # Extract data from observation
            name = observation.name
            category = categorize_observation(name)
            value = observation.data[0].value if observation.data else None
            unit = observation.data[0].unit if observation.data else None
            date = observation.date
            source_name = observation.source_name
            file_source = str(cda_file)
            
            if value is not None:  # Skip observations without values
                batch.append((name, category, value, unit, date, source_name, file_source))
                total_count += 1
                
                # Insert batch when it reaches batch_size
                if len(batch) >= batch_size:
                    conn.executemany("""
                        INSERT INTO cda_observations 
                        (name, category, value, unit, date, source_name, file_source)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, batch)
                    conn.commit()
                    batch.clear()
                    
                    if total_count % 10000 == 0:
                        elapsed = time.time() - start_time
                        rate = total_count / elapsed
                        print(f"  Processed {total_count:,} observations ({rate:.0f} obs/sec)")
        
        # Insert remaining batch
        if batch:
            conn.executemany("""
                INSERT INTO cda_observations 
                (name, category, value, unit, date, source_name, file_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            
    except Exception as e:
        print(f"Error processing file: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    elapsed = time.time() - start_time
    print(f"\nCompleted! Processed {total_count:,} observations in {elapsed:.1f} seconds")
    print(f"Database created: {db_path}")


def get_database_stats(db_path: Path) -> None:
    """
    Print statistics about the database contents.
    """
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    
    # Total observations
    cursor = conn.execute("SELECT COUNT(*) FROM cda_observations")
    total = cursor.fetchone()[0]
    print(f"Total observations: {total:,}")
    
    # By category
    print("\nObservations by category:")
    cursor = conn.execute("""
        SELECT category, COUNT(*) as count 
        FROM cda_observations 
        GROUP BY category 
        ORDER BY count DESC
    """)
    for category, count in cursor.fetchall():
        print(f"  {count:>8,} - {category}")
    
    # By observation type
    print("\nTop observation types:")
    cursor = conn.execute("""
        SELECT name, COUNT(*) as count 
        FROM cda_observations 
        GROUP BY name 
        ORDER BY count DESC
        LIMIT 10
    """)
    for name, count in cursor.fetchall():
        print(f"  {count:>8,} - {name}")
    
    # By source
    print("\nBy data source:")
    cursor = conn.execute("""
        SELECT source_name, COUNT(*) as count 
        FROM cda_observations 
        GROUP BY source_name 
        ORDER BY count DESC
    """)
    for source, count in cursor.fetchall():
        print(f"  {count:>8,} - {source}")
    
    # Date range
    cursor = conn.execute("""
        SELECT MIN(date) as min_date, MAX(date) as max_date 
        FROM cda_observations
    """)
    min_date, max_date = cursor.fetchone()
    print(f"\nDate range: {min_date} to {max_date}")
    
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Preprocess CDA XML file into SQLite database")
    parser.add_argument("cda_file", help="Path to CDA XML file (e.g., export_cda.xml)")
    parser.add_argument("-o", "--output", help="Output SQLite database file", 
                       default="cda_observations.db")
    parser.add_argument("--stats", action="store_true", 
                       help="Show statistics for existing database")
    parser.add_argument("--batch-size", type=int, default=1000,
                       help="Batch size for database inserts")
    
    args = parser.parse_args()
    
    cda_file = Path(args.cda_file)
    db_path = Path(args.output)
    
    if args.stats:
        get_database_stats(db_path)
        return
    
    if not cda_file.exists():
        print(f"CDA file not found: {cda_file}")
        sys.exit(1)
    
    if db_path.exists():
        response = input(f"Database {db_path} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(1)
        db_path.unlink()
    
    try:
        process_cda_file(cda_file, db_path, args.batch_size)
        print("\nDatabase statistics:")
        get_database_stats(db_path)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        if db_path.exists():
            db_path.unlink()
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        if db_path.exists():
            db_path.unlink()
        sys.exit(1)


if __name__ == "__main__":
    main()