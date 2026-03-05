"""
Apple Health export.xml preprocessor

Processes the massive Apple Health export.xml file and creates a SQLite database
for efficient querying and visualization.

Usage:
    python preprocess_apple_health.py /path/to/export.xml
"""

import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import argparse
from typing import Dict, Optional
import re

import config


def create_database_schema(conn: sqlite3.Connection):
    """Create SQLite database schema for Apple Health data"""
    
    # Records table - main health measurements
    conn.execute("""
        CREATE TABLE IF NOT EXISTS apple_health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            unit TEXT,
            value REAL,
            source_name TEXT NOT NULL,
            source_version TEXT,
            device TEXT,
            creation_date TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            UNIQUE(type, start_date, end_date, source_name, value)
        )
    """)
    
    # Activity summaries - daily activity rings data
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_components TEXT NOT NULL UNIQUE,
            active_energy_burned REAL,
            active_energy_burned_goal REAL,
            active_energy_burned_unit TEXT,
            apple_move_time REAL,
            apple_move_time_goal REAL,
            apple_exercise_time REAL,
            apple_exercise_time_goal REAL,
            apple_stand_hours INTEGER,
            apple_stand_hours_goal INTEGER
        )
    """)
    
    # Workouts table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_activity_type TEXT NOT NULL,
            duration REAL,
            duration_unit TEXT,
            total_distance REAL,
            total_distance_unit TEXT,
            total_energy_burned REAL,
            total_energy_burned_unit TEXT,
            source_name TEXT NOT NULL,
            source_version TEXT,
            device TEXT,
            creation_date TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL
        )
    """)
    
    # Workout statistics
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workout_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER,
            type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            average REAL,
            minimum REAL,
            maximum REAL,
            sum REAL,
            unit TEXT,
            FOREIGN KEY (workout_id) REFERENCES workouts (id)
        )
    """)
    
    # Metadata entries for all record types
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metadata_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_type TEXT NOT NULL,  -- 'record', 'workout', 'activity_summary'
            record_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL
        )
    """)
    
    # Create indexes for performance
    conn.execute("CREATE INDEX IF NOT EXISTS idx_records_type ON apple_health_records(type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_records_date ON apple_health_records(start_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_records_source ON apple_health_records(source_name)")
    # Covering index for categories query - optimizes GROUP BY type with COUNT(*)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_records_type_covering ON apple_health_records(type, id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_date ON activity_summaries(date_components)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts(start_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_metadata_record ON metadata_entries(record_type, record_id)")
    
    conn.commit()


def parse_date_safely(date_str: str) -> Optional[str]:
    """Parse Apple Health date format safely"""
    if not date_str:
        return None
    try:
        # Apple Health format: "2024-08-30 01:15:52 -0700"
        # Convert to ISO format for consistent storage
        dt = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
        return dt.isoformat()
    except ValueError:
        return date_str  # Return as-is if parsing fails


def safe_float(value: str) -> Optional[float]:
    """Safely convert string to float"""
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def safe_int(value: str) -> Optional[int]:
    """Safely convert string to int"""
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def process_xml_file(xml_path: Path, db_path: Path):
    """Process Apple Health export.xml file using streaming parser"""
    
    print(f"Processing {xml_path} -> {db_path}")
    print("This may take several minutes for large files...")
    
    # Create/connect to database
    conn = sqlite3.connect(db_path)
    create_database_schema(conn)
    
    # Counters for progress reporting
    records_processed = 0
    activities_processed = 0
    workouts_processed = 0
    batch_size = 10000
    
    try:
        # Use iterparse for memory-efficient processing of large XML
        context = ET.iterparse(xml_path, events=('start', 'end'))
        context = iter(context)
        event, root = next(context)
        
        current_workout_id = None
        record_batch = []
        metadata_batch = []
        
        for event, elem in context:
            if event == 'end':
                
                if elem.tag == 'Record':
                    # Process health record
                    record_data = (
                        elem.get('type'),
                        elem.get('unit'),
                        safe_float(elem.get('value')),
                        elem.get('sourceName'),
                        elem.get('sourceVersion'),
                        elem.get('device'),
                        parse_date_safely(elem.get('creationDate')),
                        parse_date_safely(elem.get('startDate')),
                        parse_date_safely(elem.get('endDate'))
                    )
                    record_batch.append(record_data)
                    
                    # Process metadata entries for this record
                    for metadata in elem.findall('MetadataEntry'):
                        key = metadata.get('key')
                        value = metadata.get('value')
                        if key and value:  # Only add if both key and value exist
                            metadata_batch.append((
                                'record',
                                records_processed + len(record_batch),  # Will be the record ID
                                key,
                                value
                            ))
                    
                    records_processed += 1
                    
                elif elem.tag == 'ActivitySummary':
                    # Process daily activity summary
                    try:
                        conn.execute("""
                            INSERT OR REPLACE INTO activity_summaries (
                                date_components, active_energy_burned, active_energy_burned_goal,
                                active_energy_burned_unit, apple_move_time, apple_move_time_goal,
                                apple_exercise_time, apple_exercise_time_goal, apple_stand_hours,
                                apple_stand_hours_goal
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            elem.get('dateComponents'),
                            safe_float(elem.get('activeEnergyBurned')),
                            safe_float(elem.get('activeEnergyBurnedGoal')),
                            elem.get('activeEnergyBurnedUnit'),
                            safe_float(elem.get('appleMoveTime')),
                            safe_float(elem.get('appleMoveTimeGoal')),
                            safe_float(elem.get('appleExerciseTime')),
                            safe_float(elem.get('appleExerciseTimeGoal')),
                            safe_int(elem.get('appleStandHours')),
                            safe_int(elem.get('appleStandHoursGoal'))
                        ))
                        activities_processed += 1
                    except sqlite3.IntegrityError:
                        pass  # Duplicate entry
                        
                elif elem.tag == 'Workout':
                    # Process workout
                    cursor = conn.execute("""
                        INSERT INTO workouts (
                            workout_activity_type, duration, duration_unit, total_distance,
                            total_distance_unit, total_energy_burned, total_energy_burned_unit,
                            source_name, source_version, device, creation_date, start_date, end_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        elem.get('workoutActivityType'),
                        safe_float(elem.get('duration')),
                        elem.get('durationUnit'),
                        safe_float(elem.get('totalDistance')),
                        elem.get('totalDistanceUnit'),
                        safe_float(elem.get('totalEnergyBurned')),
                        elem.get('totalEnergyBurnedUnit'),
                        elem.get('sourceName'),
                        elem.get('sourceVersion'),
                        elem.get('device'),
                        parse_date_safely(elem.get('creationDate')),
                        parse_date_safely(elem.get('startDate')),
                        parse_date_safely(elem.get('endDate'))
                    ))
                    current_workout_id = cursor.lastrowid
                    
                    # Process workout statistics
                    for stat in elem.findall('WorkoutStatistics'):
                        stat_type = stat.get('type')
                        if stat_type:  # Only process if type exists
                            conn.execute("""
                                INSERT INTO workout_statistics (
                                    workout_id, type, start_date, end_date, average, minimum, maximum, sum, unit
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                current_workout_id,
                                stat_type,
                                parse_date_safely(stat.get('startDate')),
                                parse_date_safely(stat.get('endDate')),
                                safe_float(stat.get('average')),
                                safe_float(stat.get('minimum')),
                                safe_float(stat.get('maximum')),
                                safe_float(stat.get('sum')),
                                stat.get('unit')
                            ))
                    
                    # Process workout metadata
                    for metadata in elem.findall('MetadataEntry'):
                        key = metadata.get('key')
                        value = metadata.get('value')
                        if key and value:  # Only add if both key and value exist
                            conn.execute("""
                                INSERT INTO metadata_entries (record_type, record_id, key, value)
                                VALUES (?, ?, ?, ?)
                            """, (
                                'workout',
                                current_workout_id,
                                key,
                                value
                            ))
                    
                    workouts_processed += 1
                
                # Batch insert records for performance
                if len(record_batch) >= batch_size:
                    conn.executemany("""
                        INSERT OR IGNORE INTO apple_health_records (
                            type, unit, value, source_name, source_version, device,
                            creation_date, start_date, end_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, record_batch)
                    
                    # Insert metadata batch
                    if metadata_batch:
                        conn.executemany("""
                            INSERT INTO metadata_entries (record_type, record_id, key, value)
                            VALUES (?, ?, ?, ?)
                        """, metadata_batch)
                    
                    conn.commit()
                    record_batch = []
                    metadata_batch = []
                    
                    if records_processed % 50000 == 0:
                        print(f"Processed {records_processed:,} records, {activities_processed:,} activities, {workouts_processed:,} workouts...")
                
                # Clear processed element to save memory
                elem.clear()
                # Keep root clear too
                root.clear()
        
        # Process remaining batch
        if record_batch:
            conn.executemany("""
                INSERT OR IGNORE INTO apple_health_records (
                    type, unit, value, source_name, source_version, device,
                    creation_date, start_date, end_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, record_batch)
            
            if metadata_batch:
                conn.executemany("""
                    INSERT INTO metadata_entries (record_type, record_id, key, value)
                    VALUES (?, ?, ?, ?)
                """, metadata_batch)
        
        conn.commit()
        
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        return False
    except Exception as e:
        print(f"Error processing file: {e}")
        return False
    finally:
        conn.close()
    
    print(f"\nProcessing complete!")
    print(f"- {records_processed:,} health records processed")
    print(f"- {activities_processed:,} activity summaries processed") 
    print(f"- {workouts_processed:,} workouts processed")
    print(f"- Database saved to: {db_path}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Process Apple Health export.xml file.")
    parser.add_argument('--xml_file', help='Path to Apple Health export.xml file' +
        '"\n\tDefaults to export.xml in _source_dir from config.py')
    parser.add_argument('--db', default='apple_health.db', help='Output database file (default: apple_health.db)')
    
    args = parser.parse_args()
    if args.xml_file:
        xml_path = Path(args.xml_file)
    else:
        xml_path = config.get_source_dir() / "export.xml"

    if not xml_path.exists():
        print(f"Error: XML file not found: {xml_path}")
        sys.exit(1)
    
    db_path = Path(args.db)
    
    success = process_xml_file(xml_path, db_path)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()