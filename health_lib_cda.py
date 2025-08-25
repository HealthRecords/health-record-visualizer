"""
CDA (Clinical Document Architecture) specific data access functions for SQLite database.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

import config


@dataclass
class CDAObservation:
    """Data class for CDA observations from database"""
    id: int
    name: str
    category: str
    value: float
    unit: str
    date: str
    source_name: str
    file_source: str


@dataclass
class CDACategory:
    """Data class for CDA observation categories"""
    name: str
    count: int
    url: str


def get_cda_connection() -> sqlite3.Connection:
    """Get connection to CDA database"""
    db_path = config.get_cda_database_path()
    if not db_path.exists():
        raise FileNotFoundError(f"CDA database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn


def list_cda_categories() -> List[CDACategory]:
    """List all CDA observation categories with counts"""
    if not config.has_cda_database():
        return []
    
    conn = get_cda_connection()
    cursor = conn.execute("""
        SELECT category, COUNT(*) as count 
        FROM cda_observations 
        GROUP BY category 
        ORDER BY count DESC
    """)
    
    categories = []
    for row in cursor.fetchall():
        category_name = row['category']
        count = row['count']
        # URL-safe category name for routing
        url_safe_name = category_name.lower().replace(' ', '-')
        url = f"/cda/{url_safe_name}"
        
        categories.append(CDACategory(
            name=category_name,
            count=count,
            url=url
        ))
    
    conn.close()
    return categories


def list_cda_observation_types(category: str) -> List[Tuple[str, int]]:
    """List observation types within a category with counts"""
    if not config.has_cda_database():
        return []
    
    conn = get_cda_connection()
    cursor = conn.execute("""
        SELECT name, COUNT(*) as count 
        FROM cda_observations 
        WHERE category = ?
        GROUP BY name 
        ORDER BY count DESC
    """, (category,))
    
    types = [(row['name'], row['count']) for row in cursor.fetchall()]
    conn.close()
    return types


def get_cda_observations(category: str, observation_name: Optional[str] = None, 
                        limit: Optional[int] = None) -> List[CDAObservation]:
    """Get CDA observations, optionally filtered by category and observation name"""
    if not config.has_cda_database():
        return []
    
    conn = get_cda_connection()
    
    if observation_name:
        query = """
            SELECT * FROM cda_observations 
            WHERE category = ? AND name = ?
            ORDER BY date DESC
        """
        params = (category, observation_name)
    else:
        query = """
            SELECT * FROM cda_observations 
            WHERE category = ?
            ORDER BY date DESC
        """
        params = (category,)
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor = conn.execute(query, params)
    
    observations = []
    for row in cursor.fetchall():
        obs = CDAObservation(
            id=row['id'],
            name=row['name'],
            category=row['category'],
            value=row['value'],
            unit=row['unit'],
            date=row['date'],
            source_name=row['source_name'],
            file_source=row['file_source']
        )
        observations.append(obs)
    
    conn.close()
    return observations


def get_cda_chart_data(category: str, observation_name: str) -> Dict:
    """Get chart data for a specific CDA observation type"""
    if not config.has_cda_database():
        return {"data": [], "labels": []}
    
    conn = get_cda_connection()
    cursor = conn.execute("""
        SELECT date, value, source_name 
        FROM cda_observations 
        WHERE category = ? AND name = ?
        ORDER BY date ASC
    """, (category, observation_name))
    
    data = []
    labels = []
    sources = {}
    
    for row in cursor.fetchall():
        date = row['date']
        value = row['value']
        source = row['source_name']
        
        labels.append(date)
        data.append(value)
        
        # Track sources for potential color coding
        if source not in sources:
            sources[source] = len(sources)
    
    conn.close()
    
    return {
        "data": data,
        "labels": labels,
        "sources": sources
    }


def get_cda_statistics() -> Dict:
    """Get general statistics about CDA database"""
    if not config.has_cda_database():
        return {}
    
    conn = get_cda_connection()
    
    # Total observations
    cursor = conn.execute("SELECT COUNT(*) as total FROM cda_observations")
    total = cursor.fetchone()['total']
    
    # Date range
    cursor = conn.execute("""
        SELECT MIN(date) as min_date, MAX(date) as max_date 
        FROM cda_observations
    """)
    date_range = cursor.fetchone()
    
    # Source counts
    cursor = conn.execute("""
        SELECT source_name, COUNT(*) as count 
        FROM cda_observations 
        GROUP BY source_name 
        ORDER BY count DESC
    """)
    sources = {row['source_name']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "total_observations": total,
        "date_range": {
            "min": date_range['min_date'],
            "max": date_range['max_date']
        },
        "sources": sources
    }


def search_cda_observations(query: str, limit: int = 100) -> List[CDAObservation]:
    """Search CDA observations by name or category"""
    if not config.has_cda_database():
        return []
    
    conn = get_cda_connection()
    cursor = conn.execute("""
        SELECT * FROM cda_observations 
        WHERE name LIKE ? OR category LIKE ? OR source_name LIKE ?
        ORDER BY date DESC
        LIMIT ?
    """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
    
    observations = []
    for row in cursor.fetchall():
        obs = CDAObservation(
            id=row['id'],
            name=row['name'],
            category=row['category'],
            value=row['value'],
            unit=row['unit'],
            date=row['date'],
            source_name=row['source_name'],
            file_source=row['file_source']
        )
        observations.append(obs)
    
    conn.close()
    return observations