"""
Apple Health data access functions for SQLite database.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
from datetime import datetime, timedelta
import config


@dataclass
class AppleHealthRecord:
    """Data class for Apple Health records from database"""
    id: int
    type: str
    unit: Optional[str]
    value: Optional[float]
    source_name: str
    source_version: Optional[str]
    device: Optional[str]
    creation_date: Optional[str]
    start_date: str
    end_date: str


@dataclass
class AppleHealthCategory:
    """Data class for Apple Health record categories"""
    name: str
    display_name: str
    count: int
    url: str
    icon_class: str
    icon_color: str


@dataclass
class ActivitySummary:
    """Data class for daily activity summary"""
    date: str
    active_energy_burned: Optional[float]
    active_energy_burned_goal: Optional[float]
    apple_move_time: Optional[float]
    apple_move_time_goal: Optional[float]
    apple_exercise_time: Optional[float]
    apple_exercise_time_goal: Optional[float]
    apple_stand_hours: Optional[int]
    apple_stand_hours_goal: Optional[int]


def get_apple_health_connection() -> sqlite3.Connection:
    """Get connection to Apple Health database"""
    db_path = config.get_apple_health_database_path()
    if not db_path.exists():
        raise FileNotFoundError(f"Apple Health database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn


def list_apple_health_categories() -> List[AppleHealthCategory]:
    """List all Apple Health record categories with counts"""
    if not config.has_apple_health_database():
        return []
    
    conn = get_apple_health_connection()
    
    # Get all record types with counts
    cursor = conn.execute("""
        SELECT type, COUNT(*) as count 
        FROM apple_health_records 
        GROUP BY type 
        ORDER BY count DESC
    """)
    
    categories = []
    type_mapping = get_record_type_mapping()
    
    for row in cursor.fetchall():
        record_type = row['type']
        count = row['count']
        
        # Get display info from mapping or create default
        display_info = type_mapping.get(record_type, {
            'display_name': record_type.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', ''),
            'category': 'Other',
            'icon_class': 'bi-activity',
            'icon_color': 'text-secondary'
        })
        
        # Create URL-safe name
        url_name = record_type.lower().replace('hkquantitytypeidentifier', '').replace('hkcategorytypeidentifier', '')
        
        categories.append(AppleHealthCategory(
            name=record_type,
            display_name=display_info['display_name'],
            count=count,
            url=f"/apple/{url_name}",
            icon_class=display_info['icon_class'],
            icon_color=display_info['icon_color']
        ))
    
    conn.close()
    return categories


def get_record_type_mapping() -> Dict[str, Dict[str, str]]:
    """Get mapping of Apple Health record types to display information"""
    return {
        # Activity & Fitness
        'HKQuantityTypeIdentifierStepCount': {
            'display_name': 'Step Count',
            'category': 'Activity',
            'icon_class': 'bi-person-walking',
            'icon_color': 'text-primary'
        },
        'HKQuantityTypeIdentifierDistanceWalkingRunning': {
            'display_name': 'Walking + Running Distance',
            'category': 'Activity',
            'icon_class': 'bi-speedometer',
            'icon_color': 'text-primary'
        },
        'HKQuantityTypeIdentifierFlightsClimbed': {
            'display_name': 'Flights Climbed',
            'category': 'Activity',
            'icon_class': 'bi-arrow-up',
            'icon_color': 'text-primary'
        },
        'HKQuantityTypeIdentifierActiveEnergyBurned': {
            'display_name': 'Active Energy Burned',
            'category': 'Activity',
            'icon_class': 'bi-fire',
            'icon_color': 'text-danger'
        },
        'HKQuantityTypeIdentifierBasalEnergyBurned': {
            'display_name': 'Basal Energy Burned',
            'category': 'Activity',
            'icon_class': 'bi-battery',
            'icon_color': 'text-info'
        },
        
        # Vitals
        'HKQuantityTypeIdentifierHeartRate': {
            'display_name': 'Heart Rate',
            'category': 'Vitals',
            'icon_class': 'bi-heart-pulse',
            'icon_color': 'text-danger'
        },
        'HKQuantityTypeIdentifierBloodPressureSystolic': {
            'display_name': 'Blood Pressure Systolic',
            'category': 'Vitals',
            'icon_class': 'bi-activity',
            'icon_color': 'text-warning'
        },
        'HKQuantityTypeIdentifierBloodPressureDiastolic': {
            'display_name': 'Blood Pressure Diastolic',
            'category': 'Vitals',
            'icon_class': 'bi-activity',
            'icon_color': 'text-warning'
        },
        'HKQuantityTypeIdentifierRespiratoryRate': {
            'display_name': 'Respiratory Rate',
            'category': 'Vitals',
            'icon_class': 'bi-lungs',
            'icon_color': 'text-info'
        },
        'HKQuantityTypeIdentifierOxygenSaturation': {
            'display_name': 'Oxygen Saturation',
            'category': 'Vitals',
            'icon_class': 'bi-droplet',
            'icon_color': 'text-info'
        },
        
        # Body Measurements  
        'HKQuantityTypeIdentifierBodyMass': {
            'display_name': 'Body Weight',
            'category': 'Body',
            'icon_class': 'bi-speedometer2',
            'icon_color': 'text-success'
        },
        'HKQuantityTypeIdentifierHeight': {
            'display_name': 'Height',
            'category': 'Body',
            'icon_class': 'bi-rulers',
            'icon_color': 'text-success'
        },
        'HKQuantityTypeIdentifierBodyFatPercentage': {
            'display_name': 'Body Fat Percentage',
            'category': 'Body',
            'icon_class': 'bi-percent',
            'icon_color': 'text-success'
        },
        
        # Lab Results
        'HKQuantityTypeIdentifierBloodGlucose': {
            'display_name': 'Blood Glucose',
            'category': 'Lab Results',
            'icon_class': 'bi-droplet',
            'icon_color': 'text-warning'
        },
        
        # Sleep
        'HKCategoryTypeIdentifierSleepAnalysis': {
            'display_name': 'Sleep Analysis',
            'category': 'Sleep',
            'icon_class': 'bi-moon',
            'icon_color': 'text-secondary'
        },
    }


def get_apple_health_records(record_type: str, limit: Optional[int] = None, 
                           after: Optional[str] = None, before: Optional[str] = None) -> List[AppleHealthRecord]:
    """Get Apple Health records of a specific type"""
    if not config.has_apple_health_database():
        return []
    
    conn = get_apple_health_connection()
    
    # Build query with optional filters
    query = "SELECT * FROM apple_health_records WHERE type = ?"
    params = [record_type]
    
    if after:
        query += " AND start_date >= ?"
        params.append(after)
    
    if before:
        query += " AND start_date <= ?"
        params.append(before)
    
    query += " ORDER BY start_date DESC"
    
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    
    cursor = conn.execute(query, params)
    
    records = []
    for row in cursor.fetchall():
        records.append(AppleHealthRecord(
            id=row['id'],
            type=row['type'],
            unit=row['unit'],
            value=row['value'],
            source_name=row['source_name'],
            source_version=row['source_version'],
            device=row['device'],
            creation_date=row['creation_date'],
            start_date=row['start_date'],
            end_date=row['end_date']
        ))
    
    conn.close()
    return records


def get_apple_health_statistics() -> Dict:
    """Get general statistics about Apple Health database"""
    if not config.has_apple_health_database():
        return {}
    
    conn = get_apple_health_connection()
    
    # Total records
    cursor = conn.execute("SELECT COUNT(*) as total FROM apple_health_records")
    total_records = cursor.fetchone()['total']
    
    # Total activity summaries
    cursor = conn.execute("SELECT COUNT(*) as total FROM activity_summaries")
    total_activities = cursor.fetchone()['total']
    
    # Total workouts
    cursor = conn.execute("SELECT COUNT(*) as total FROM workouts")
    total_workouts = cursor.fetchone()['total']
    
    # Date range
    cursor = conn.execute("""
        SELECT MIN(start_date) as min_date, MAX(start_date) as max_date 
        FROM apple_health_records
    """)
    date_range = cursor.fetchone()
    
    # Source counts
    cursor = conn.execute("""
        SELECT source_name, COUNT(*) as count 
        FROM apple_health_records 
        GROUP BY source_name 
        ORDER BY count DESC
    """)
    sources = {row['source_name']: row['count'] for row in cursor.fetchall()}
    
    # Record type counts
    cursor = conn.execute("""
        SELECT type, COUNT(*) as count 
        FROM apple_health_records 
        GROUP BY type 
        ORDER BY count DESC
        LIMIT 10
    """)
    top_types = {row['type']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "total_records": total_records,
        "total_activities": total_activities,
        "total_workouts": total_workouts,
        "date_range": {
            "min": date_range['min_date'],
            "max": date_range['max_date']
        },
        "sources": sources,
        "top_record_types": top_types
    }


def get_activity_summaries(limit: Optional[int] = None, 
                         after: Optional[str] = None, 
                         before: Optional[str] = None) -> List[ActivitySummary]:
    """Get daily activity summaries"""
    if not config.has_apple_health_database():
        return []
    
    conn = get_apple_health_connection()
    
    # Build query with optional filters
    query = "SELECT * FROM activity_summaries"
    params = []
    where_clauses = []
    
    if after:
        where_clauses.append("date_components >= ?")
        params.append(after)
    
    if before:
        where_clauses.append("date_components <= ?")
        params.append(before)
    
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    query += " ORDER BY date_components DESC"
    
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    
    cursor = conn.execute(query, params)
    
    summaries = []
    for row in cursor.fetchall():
        summaries.append(ActivitySummary(
            date=row['date_components'],
            active_energy_burned=row['active_energy_burned'],
            active_energy_burned_goal=row['active_energy_burned_goal'],
            apple_move_time=row['apple_move_time'],
            apple_move_time_goal=row['apple_move_time_goal'],
            apple_exercise_time=row['apple_exercise_time'],
            apple_exercise_time_goal=row['apple_exercise_time_goal'],
            apple_stand_hours=row['apple_stand_hours'],
            apple_stand_hours_goal=row['apple_stand_hours_goal']
        ))
    
    conn.close()
    return summaries


def get_record_data_for_chart(record_type: str, bucket_size: str = 'hour',
                            after: Optional[str] = None, before: Optional[str] = None) -> List[Dict]:
    """Get aggregated record data for charting with automatic bucketing"""
    if not config.has_apple_health_database():
        return []
    
    conn = get_apple_health_connection()
    
    # Determine bucketing based on data volume and time range
    # First, get total count and date range for this record type
    count_query = "SELECT COUNT(*) as count, MIN(start_date) as min_date, MAX(start_date) as max_date FROM apple_health_records WHERE type = ?"
    params = [record_type]
    
    if after:
        count_query += " AND start_date >= ?"
        params.append(after)
    if before:
        count_query += " AND start_date <= ?"
        params.append(before)
    
    cursor = conn.execute(count_query, params)
    result = cursor.fetchone()
    total_count = result['count']
    
    # Auto-select bucket size based on data volume
    if total_count > 10000:
        bucket_format = '%Y-%m-%d'  # Daily
        bucket_size = 'day'
    elif total_count > 1000:
        bucket_format = '%Y-%m-%d %H:00:00'  # Hourly
        bucket_size = 'hour'
    else:
        bucket_format = '%Y-%m-%d %H:%M:00'  # Minute
        bucket_size = 'minute'
    
    # Build aggregated query
    query = f"""
        SELECT 
            strftime('{bucket_format}', start_date) as time_bucket,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value,
            COUNT(*) as count,
            unit
        FROM apple_health_records 
        WHERE type = ? AND value IS NOT NULL
    """
    params = [record_type]
    
    if after:
        query += " AND start_date >= ?"
        params.append(after)
    if before:
        query += " AND start_date <= ?"
        params.append(before)
    
    query += " GROUP BY time_bucket, unit ORDER BY time_bucket"
    
    cursor = conn.execute(query, params)
    
    data_points = []
    for row in cursor.fetchall():
        data_points.append({
            'date': row['time_bucket'],
            'value': row['avg_value'],
            'min_value': row['min_value'],
            'max_value': row['max_value'],
            'count': row['count'],
            'unit': row['unit']
        })
    
    conn.close()
    return data_points