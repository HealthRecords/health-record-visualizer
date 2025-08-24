"""
FastAPI Health Data Explorer

A web interface for exploring health data from Apple Health exports.
Provides the same functionality as the text-based menu system with a modern web UI.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import glob
from datetime import datetime
from io import StringIO
import csv

import config
from health_lib import (
    list_prefixes, list_categories, list_vitals, 
    yield_observation_files, extract_all_values, StatInfo,
    ValueString
)
from health import print_conditions, print_medicines, print_procedures
from models import (
    PrefixResponse, CategoryResponse, VitalResponse, 
    ObservationDataResponse, ChartDataResponse,
    ConditionsResponse, MedicationsResponse, ProceduresResponse,
    ConditionRecord, MedicationRecord, ProcedureRecord,
    ReferenceRange
)

app = FastAPI(
    title="Health Data Explorer",
    description="Web interface for exploring Apple Health data exports",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Health data paths
def get_health_paths():
    """Get the base path and clinical records path for health data"""
    base_path = config.get_source_dir()
    clinical_path = base_path / "clinical-records"
    return base_path, clinical_path

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """Homepage with main navigation menu"""
    try:
        _, clinical_path = get_health_paths()
        prefixes = list_prefixes(clinical_path)
        
        # Convert to list of dicts for template
        menu_items = [
            {"name": prefix, "count": count, "url": get_menu_url(prefix)}
            for prefix, count in prefixes.items()
        ]
        
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request, 
                "menu_items": menu_items,
                "title": "Health Data Explorer",
                "total_files": sum(prefixes.values())
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading homepage: {str(e)}")

def get_menu_url(prefix: str) -> str:
    """Generate appropriate URL for each data type"""
    url_map = {
        "Observation": "/observations",
        "Condition": "/conditions", 
        "MedicationRequest": "/medications",
        "Procedure": "/procedures",
        "AllergyIntolerance": "/allergies",
        "DocumentReference": "/documents",
        "DiagnosticReport": "/diagnosticreports"
    }
    return url_map.get(prefix, f"/data/{prefix.lower()}")


@app.get("/api/prefixes")
async def get_prefixes() -> PrefixResponse:
    """Get available data file prefixes"""
    try:
        _, clinical_path = get_health_paths()
        prefixes = list_prefixes(clinical_path)
        return PrefixResponse(prefixes=prefixes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting prefixes: {str(e)}")

@app.get("/observations", response_class=HTMLResponse)
async def observations_page(request: Request):
    """Observations main page showing categories"""
    try:
        _, clinical_path = get_health_paths()
        categories, counter, file_count = list_categories(clinical_path, False, one_prefix="Observation")
        
        # Convert to list of dicts for template with counts
        category_items = [
            {"name": category, "count": counter[category], "url": f"/observations/{category.lower().replace(' ', '-')}"}
            for category in categories
        ]
        
        return templates.TemplateResponse(
            "observations.html",
            {
                "request": request,
                "categories": category_items,
                "title": "Observations",
                "file_count": file_count,
                "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "Observations", "url": "/observations"}]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading observations: {str(e)}")

@app.get("/api/observations/categories")
async def get_observation_categories() -> CategoryResponse:
    """Get available observation categories"""
    try:
        _, clinical_path = get_health_paths()
        categories, counter, file_count = list_categories(clinical_path, False, one_prefix="Observation")
        return CategoryResponse(categories=categories, counts=counter, total_files=file_count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting categories: {str(e)}")

@app.get("/observations/{category}", response_class=HTMLResponse)
async def observation_category_page(request: Request, category: str):
    """Show vitals within a specific category"""
    try:
        _, clinical_path = get_health_paths()
        # Convert URL-safe category back to display format
        display_category = category.replace('-', ' ').title()
        
        vitals = list_vitals(yield_observation_files(clinical_path), display_category)
        
        # Convert to list of dicts for template  
        # Use URL-safe encoding that preserves original vital names
        import urllib.parse
        vital_items = [
            {
                "name": vital, 
                "count": count,
                "url": f"/observations/{category}/{urllib.parse.quote(vital, safe='')}"
            }
            for vital, count in sorted(vitals.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return templates.TemplateResponse(
            "vitals.html",
            {
                "request": request,
                "vitals": vital_items,
                "category": display_category,
                "title": f"{display_category} - Vitals",
                "breadcrumb": [
                    {"name": "Home", "url": "/"},
                    {"name": "Observations", "url": "/observations"},
                    {"name": display_category, "url": f"/observations/{category}"}
                ]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading category {category}: {str(e)}")

@app.get("/api/observations/{category}/vitals")
async def get_category_vitals(category: str) -> VitalResponse:
    """Get vitals for a specific category"""
    try:
        _, clinical_path = get_health_paths()
        display_category = category.replace('-', ' ').title()
        vitals = list_vitals(yield_observation_files(clinical_path), display_category)
        return VitalResponse(category=display_category, vitals=vitals)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting vitals for {category}: {str(e)}")

@app.get("/observations/{category}/{vital}", response_class=HTMLResponse)
async def vital_detail_page(request: Request, category: str, vital: str):
    """Show detailed view of a specific vital with chart and data"""
    try:
        import urllib.parse
        display_category = category.replace('-', ' ').title()
        display_vital = urllib.parse.unquote(vital)
        
        return templates.TemplateResponse(
            "vital_detail.html",
            {
                "request": request,
                "category": display_category,
                "vital": display_vital,
                "title": f"{display_vital} - {display_category}",
                "breadcrumb": [
                    {"name": "Home", "url": "/"},
                    {"name": "Observations", "url": "/observations"},
                    {"name": display_category, "url": f"/observations/{category}"},
                    {"name": display_vital, "url": f"/observations/{category}/{vital}"}
                ]
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading vital {vital}: {str(e)}")

@app.get("/api/observations/{category}/{vital}/data")
async def get_vital_data(
    category: str, 
    vital: str, 
    after: Optional[str] = None,
    before: Optional[str] = None,
    format: str = "json"
) -> ObservationDataResponse:
    """Get data for a specific vital"""
    try:
        import urllib.parse
        _, clinical_path = get_health_paths()
        display_category = category.replace('-', ' ').title()
        display_vital = urllib.parse.unquote(vital)
        
        # Extract the data using existing health_lib functions
        ws = extract_all_values(
            yield_observation_files(clinical_path), 
            stat_info=StatInfo(display_category, display_vital)
        )
        
        # Apply date filters if provided
        if after:
            after_date = datetime.strptime(after, '%Y-%m-%d')
            ws = [w for w in ws if after_date < datetime.strptime(w.date, '%Y-%m-%dT%H:%M:%SZ')]
            
        if before:
            before_date = datetime.strptime(before, '%Y-%m-%d')
            ws = [w for w in ws if datetime.strptime(w.date, '%Y-%m-%dT%H:%M:%SZ') < before_date]
        
        # Sort observations by date (most recent first)
        ws.sort(key=lambda x: x.date, reverse=True)
        
        # Convert to response format
        data_points = []
        for observation in ws:
            # Convert reference range if available
            ref_range = None
            if observation.range:
                ref_range = ReferenceRange(
                    low=observation.range.low.value if observation.range.low else None,
                    high=observation.range.high.value if observation.range.high else None,
                    text=observation.range.text,
                    unit=observation.range.low.unit if observation.range.low else None
                )
            
            for value in observation.data:
                # Check if this is a numeric or text value
                if hasattr(value, 'unit'):  # ValueQuantity
                    data_points.append({
                        "date": observation.date,
                        "value": value.value,
                        "text_value": None,
                        "unit": value.unit,
                        "name": value.name,
                        "reference_range": ref_range,
                        "is_text": False
                    })
                else:  # ValueString
                    data_points.append({
                        "date": observation.date,
                        "value": None,
                        "text_value": value.value,
                        "unit": None,
                        "name": value.name,
                        "reference_range": None,  # Text values don't have reference ranges
                        "is_text": True
                    })
        
        return ObservationDataResponse(
            category=display_category,
            vital=display_vital,
            data=data_points,
            count=len(data_points)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting data for {vital}: {str(e)}")

@app.get("/api/observations/{category}/{vital}/chart")
async def get_chart_data(category: str, vital: str, after: Optional[str] = None, before: Optional[str] = None) -> ChartDataResponse:
    """Get chart configuration data for ECharts"""
    try:
        import urllib.parse
        _, clinical_path = get_health_paths()
        display_category = category.replace('-', ' ').title()
        display_vital = urllib.parse.unquote(vital)
        
        # Extract the data
        ws = extract_all_values(
            yield_observation_files(clinical_path), 
            stat_info=StatInfo(display_category, display_vital)
        )
        
        # Apply date filters if provided
        if after:
            after_date = datetime.strptime(after, '%Y-%m-%d')
            ws = [w for w in ws if after_date < datetime.strptime(w.date, '%Y-%m-%dT%H:%M:%SZ')]
            
        if before:
            before_date = datetime.strptime(before, '%Y-%m-%d')
            ws = [w for w in ws if datetime.strptime(w.date, '%Y-%m-%dT%H:%M:%SZ') < before_date]
        
        if not ws:
            return ChartDataResponse(
                title=display_vital,
                dates=[],
                series=[],
                chart_config={}
            )
        
        # Check if this is a text-based observation that can't be charted
        first = ws[0]
        if first.data and not hasattr(first.data[0], 'unit'):
            # This is a text-based observation, return empty chart config
            return ChartDataResponse(
                title=display_vital,
                dates=[],
                series=[],
                chart_config={
                    "title": {
                        "text": display_vital,
                        "subtext": "Text-based results cannot be charted. View data table below for results.",
                        "left": "center",
                        "top": "middle",
                        "textStyle": {
                            "fontSize": 18
                        },
                        "subtextStyle": {
                            "fontSize": 14,
                            "color": "#666"
                        }
                    },
                    "xAxis": {
                        "show": False
                    },
                    "yAxis": {
                        "show": False
                    }
                }
            )
        
        # Sort observations by date (oldest first) for proper chart timeline
        ws.sort(key=lambda x: x.date, reverse=False)
        
        # Prepare chart data
        dates = [observation.date for observation in ws]
        
        # Handle single vs multi-value observations
        first = ws[0]
        series = []
        
        if len(first.data) == 1:
            # Single value (like Weight, Height)  
            # Convert ISO date strings to millisecond timestamps for ECharts
            data_pairs = []
            for observation in ws:
                timestamp = int(datetime.strptime(observation.date, '%Y-%m-%dT%H:%M:%SZ').timestamp() * 1000)
                data_pairs.append([timestamp, observation.data[0].value])
            
            series.append({
                "name": display_vital,
                "data": data_pairs,
                "type": "line"
            })
        elif len(first.data) == 2:
            # Two values (like Blood Pressure)
            # Convert ISO date strings to millisecond timestamps for ECharts
            data_pairs_1 = []
            data_pairs_2 = []
            for observation in ws:
                timestamp = int(datetime.strptime(observation.date, '%Y-%m-%dT%H:%M:%SZ').timestamp() * 1000)
                data_pairs_1.append([timestamp, observation.data[0].value])
                data_pairs_2.append([timestamp, observation.data[1].value])
            
            series.append({
                "name": first.data[0].name,
                "data": data_pairs_1,
                "type": "line"
            })
            series.append({
                "name": first.data[1].name,
                "data": data_pairs_2,
                "type": "line"
            })
        
        # Check for reference range to add to chart
        reference_range = None
        if ws and ws[0].range and ws[0].range.low and ws[0].range.high:
            reference_range = {
                "low": ws[0].range.low.value,
                "high": ws[0].range.high.value,
                "text": ws[0].range.text
            }
        
        # Generate ECharts configuration
        chart_config = {
            "title": {
                "text": display_vital,
                "left": "center"
            },
            "tooltip": {
                "trigger": "axis"
            },
            "legend": {
                "top": "30"
            },
            "xAxis": {
                "type": "time",
                "axisLabel": {
                    "formatter": "{yyyy}-{MM}-{dd}",
                    "rotate": 45
                },
                "splitLine": {
                    "show": True
                }
            },
            "yAxis": {
                "type": "value"
            },
            "series": series
        }
        
        # Add reference range bands and adjust y-axis if available
        if reference_range:
            # Calculate data range
            all_values = []
            for s in series:
                all_values.extend([point[1] for point in s["data"]])
            
            if all_values:
                data_min = min(all_values)
                data_max = max(all_values)
                ref_min = reference_range["low"]
                ref_max = reference_range["high"]
                
                # Extend y-axis to include both data and reference range with some padding
                y_min = min(data_min, ref_min)
                y_max = max(data_max, ref_max)
                padding = (y_max - y_min) * 0.1  # 10% padding
                
                chart_config["yAxis"]["min"] = max(0, y_min - padding)  # Don't go below 0 for health data
                chart_config["yAxis"]["max"] = y_max + padding
            # Add reference range as a background area for each series
            for i, s in enumerate(series):
                series[i]["markArea"] = {
                    "silent": True,
                    "itemStyle": {
                        "color": "rgba(173, 216, 230, 0.2)"  # Light blue background
                    },
                    "label": {
                        "show": True if i == 0 else False,  # Only show label on first series
                        "formatter": f"Normal Range\n{reference_range['text']}"
                    },
                    "data": [
                        [
                            {"yAxis": reference_range["low"]},
                            {"yAxis": reference_range["high"]}
                        ]
                    ]
                }
        
        return ChartDataResponse(
            title=display_vital,
            dates=dates,
            series=series,
            chart_config=chart_config
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chart for {vital}: {str(e)}")

# Medical Records Endpoints
@app.get("/conditions", response_class=HTMLResponse)
async def conditions_page(request: Request):
    """Conditions page"""
    return templates.TemplateResponse(
        "conditions.html",
        {
            "request": request,
            "title": "Conditions",
            "api_endpoint": "/api/conditions",
            "resource_type": "conditions",
            "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "Conditions", "url": "/conditions"}]
        }
    )

@app.get("/api/conditions")
async def get_conditions() -> ConditionsResponse:
    """Get all conditions data"""
    try:
        _, clinical_path = get_health_paths()
        path = clinical_path / "Condition*.json"
        conditions = []
        
        for p in glob.glob(str(path)):
            with open(p) as f:
                condition = json.load(f)
                conditions.append(ConditionRecord(
                    resource_type=condition['resourceType'],
                    recorded_date=condition['recordedDate'],
                    clinical_status=condition['clinicalStatus']['coding'][0]['code'],
                    verification_status=condition['verificationStatus']['coding'][0]['code'],
                    condition_text=condition['code']['text']
                ))
        
        # Sort by recorded date (most recent first)
        conditions.sort(key=lambda x: x.recorded_date, reverse=True)
        
        return ConditionsResponse(conditions=conditions, count=len(conditions))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading conditions: {str(e)}")

@app.get("/medications", response_class=HTMLResponse)
async def medications_page(request: Request):
    """Medications page"""
    return templates.TemplateResponse(
        "medications.html",
        {
            "request": request,
            "title": "Medications", 
            "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "Medications", "url": "/medications"}]
        }
    )

@app.get("/api/medications")
async def get_medications(include_inactive: bool = False) -> MedicationsResponse:
    """Get all medications data"""
    try:
        _, clinical_path = get_health_paths()
        path = clinical_path / "MedicationRequest*.json"
        medications = []
        
        for p in glob.glob(str(path)):
            with open(p) as f:
                medication = json.load(f)
                is_active = not medication['status'] in ['completed', 'stopped']
                
                if is_active or include_inactive:
                    medications.append(MedicationRecord(
                        resource_type=medication['resourceType'],
                        authored_date=medication['authoredOn'],
                        status=medication['status'],
                        medication_name=medication['medicationReference']['display']
                    ))
        
        # Sort by authored date (most recent first)
        medications.sort(key=lambda x: x.authored_date, reverse=True)
        
        return MedicationsResponse(
            medications=medications, 
            count=len(medications),
            include_inactive=include_inactive
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading medications: {str(e)}")

@app.get("/procedures", response_class=HTMLResponse)
async def procedures_page(request: Request):
    """Procedures page"""
    return templates.TemplateResponse(
        "procedures.html",
        {
            "request": request,
            "title": "Procedures",
            "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "Procedures", "url": "/procedures"}]
        }
    )

@app.get("/api/procedures")
async def get_procedures() -> ProceduresResponse:
    """Get all procedures data"""
    try:
        _, clinical_path = get_health_paths()
        path = clinical_path / "Procedure*.json"
        procedures = []
        
        for p in glob.glob(str(path)):
            with open(p) as f:
                procedure = json.load(f)
                
                # Handle different date formats (performedDateTime vs performedPeriod)
                performed_date = procedure.get('performedDateTime')
                if not performed_date and 'performedPeriod' in procedure:
                    performed_date = procedure['performedPeriod'].get('start', 'Unknown')
                if not performed_date:
                    performed_date = 'Unknown'
                
                procedures.append(ProcedureRecord(
                    resource_type=procedure['resourceType'],
                    performed_date=performed_date,
                    status=procedure.get('status', 'Unknown'),
                    procedure_text=procedure.get('code', {}).get('text', 'Unknown Procedure')
                ))
        
        # Sort by performed date (most recent first)
        procedures.sort(key=lambda x: x.performed_date, reverse=True)
        
        return ProceduresResponse(procedures=procedures, count=len(procedures))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading procedures: {str(e)}")

# Additional API endpoint for allergies (AllergyIntolerance)
@app.get("/allergies", response_class=HTMLResponse)
async def allergies_page(request: Request):
    """Allergies page"""
    return templates.TemplateResponse(
        "conditions.html",  # Reuse conditions template since structure is similar
        {
            "request": request,
            "title": "Allergies",
            "api_endpoint": "/api/allergies",
            "resource_type": "allergies",
            "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "Allergies", "url": "/allergies"}]
        }
    )

@app.get("/api/allergies")
async def get_allergies() -> ConditionsResponse:
    """Get all allergies data"""
    try:
        _, clinical_path = get_health_paths()
        path = clinical_path / "AllergyIntolerance*.json"
        allergies = []
        
        for p in glob.glob(str(path)):
            with open(p) as f:
                allergy = json.load(f)
                allergies.append(ConditionRecord(
                    resource_type=allergy['resourceType'],
                    recorded_date=allergy['recordedDate'],
                    clinical_status=allergy['clinicalStatus']['coding'][0]['code'],
                    verification_status=allergy['verificationStatus']['coding'][0]['code'],
                    condition_text=allergy['code']['text']
                ))
        
        # Sort by recorded date (most recent first)
        allergies.sort(key=lambda x: x.recorded_date, reverse=True)
        
        return ConditionsResponse(conditions=allergies, count=len(allergies))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading allergies: {str(e)}")

@app.get("/diagnosticreports", response_class=HTMLResponse)
async def diagnosticreports_page(request: Request):
    """Diagnostic reports page"""
    return templates.TemplateResponse(
        "generic_data.html",  # Use generic template for better compatibility
        {
            "request": request,
            "title": "Diagnostic Reports",
            "resource_type": "DiagnosticReport",
            "api_endpoint": "/api/diagnosticreports",
            "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "Diagnostic Reports", "url": "/diagnosticreports"}]
        }
    )

@app.get("/api/diagnosticreports")
async def get_diagnosticreports():
    """Get all diagnostic reports data - basic implementation"""
    try:
        _, clinical_path = get_health_paths()
        path = clinical_path / "DiagnosticReport*.json"
        records = []
        
        for p in glob.glob(str(path)):
            with open(p) as f:
                report = json.load(f)
                # Format to match generic template expectations
                records.append({
                    "resource_type": report.get('resourceType', 'DiagnosticReport'),
                    "id": report.get('id', 'Unknown'),
                    "date": report.get('effectiveDateTime', 'Unknown'),
                    "status": report.get('status', 'Unknown'),
                    "text": report.get('code', {}).get('text', 'Unknown Report Type'),
                    "raw_data": report
                })
        
        # Sort by effective date (most recent first)
        records.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return {"records": records, "count": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading diagnostic reports: {str(e)}")

# Document Reference handler (was mapped but missing)
@app.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request):
    """Document references page"""
    return templates.TemplateResponse(
        "generic_data.html", 
        {
            "request": request,
            "title": "Document References",
            "resource_type": "DocumentReference",
            "api_endpoint": "/api/documents",
            "breadcrumb": [{"name": "Home", "url": "/"}, {"name": "Document References", "url": "/documents"}]
        }
    )

@app.get("/api/documents")
async def get_documents():
    """Get all document references data"""
    try:
        _, clinical_path = get_health_paths()
        pattern = clinical_path / "DocumentReference*.json"
        records = []
        
        for file_path in glob.glob(str(pattern)):
            with open(file_path) as f:
                record = json.load(f)
                
                records.append({
                    "resource_type": record.get('resourceType', 'DocumentReference'),
                    "id": record.get('id', 'Unknown'),
                    "date": record.get('date', 'Unknown'),
                    "status": record.get('docStatus', 'Unknown'),
                    "text": record.get('description') or record.get('type', {}).get('text', 'Document'),
                    "raw_data": record
                })
        
        # Sort by date (most recent first)
        records.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return {"records": records, "count": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading documents: {str(e)}")

# Generic route handler for unmapped resource types
@app.get("/data/{resource_type}", response_class=HTMLResponse)
async def generic_data_page(request: Request, resource_type: str):
    """Generic data page for any FHIR resource type"""
    try:
        # Find the exact resource type name from discovered prefixes
        _, clinical_path = get_health_paths()
        prefixes = list_prefixes(clinical_path)
        
        # Look for a matching resource type (case-insensitive)
        fhir_type = None
        for prefix in prefixes.keys():
            if prefix.lower() == resource_type.lower():
                fhir_type = prefix
                break
        
        if not fhir_type:
            raise HTTPException(status_code=404, detail=f"No {resource_type} data found")
        
        # Check if files exist (they should, since we found the prefix)
        pattern = clinical_path / f"{fhir_type}*.json"
        files = list(glob.glob(str(pattern)))
        
        return templates.TemplateResponse(
            "generic_data.html",
            {
                "request": request,
                "title": f"{fhir_type} Records",
                "resource_type": fhir_type,
                "api_endpoint": f"/api/data/{resource_type}",
                "count": len(files),
                "breadcrumb": [{"name": "Home", "url": "/"}, {"name": f"{fhir_type} Records", "url": f"/data/{resource_type}"}]
            }
        )
    except Exception as e:
        if "No " in str(e) and " data found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"Error loading {resource_type}: {str(e)}")

@app.get("/api/data/{resource_type}")
async def get_generic_data(resource_type: str):
    """Generic API endpoint for any FHIR resource type"""
    try:
        # Find the exact resource type name from discovered prefixes
        _, clinical_path = get_health_paths()
        prefixes = list_prefixes(clinical_path)
        
        # Look for a matching resource type (case-insensitive)
        fhir_type = None
        for prefix in prefixes.keys():
            if prefix.lower() == resource_type.lower():
                fhir_type = prefix
                break
        
        if not fhir_type:
            raise HTTPException(status_code=404, detail=f"No {resource_type} data found")
        
        pattern = clinical_path / f"{fhir_type}*.json"
        records = []
        
        for file_path in glob.glob(str(pattern)):
            with open(file_path) as f:
                record = json.load(f)
                
                # Extract common fields that most FHIR resources have
                
                # Extract date from various possible fields
                date = (record.get('recordedDate') or 
                       record.get('authoredOn') or 
                       record.get('effectiveDateTime') or 
                       record.get('performedDateTime') or 
                       'Unknown')
                
                # Extract status from various possible fields
                status = record.get('status')
                if not status and record.get('clinicalStatus'):
                    clinical_status = record.get('clinicalStatus', {})
                    coding = clinical_status.get('coding', [])
                    if coding:
                        status = coding[0].get('code')
                if not status:
                    status = 'Unknown'
                
                # Extract text description from various possible fields
                text = record.get('code', {}).get('text')
                if not text:
                    text = record.get('medicationCodeableConcept', {}).get('text')
                if not text and record.get('category'):
                    text = record.get('category', [{}])[0].get('text')
                if not text:
                    text = 'Unknown'
                
                records.append({
                    "resource_type": record.get('resourceType', fhir_type),
                    "id": record.get('id', 'Unknown'),
                    "date": date,
                    "status": status,
                    "text": text,
                    "raw_data": record  # Include full record for detailed view
                })
        
        # Sort by date (most recent first) 
        records.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return {"records": records, "count": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading {resource_type}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)