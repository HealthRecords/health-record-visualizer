"""
Pydantic models for FastAPI request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime


class PrefixResponse(BaseModel):
    """Response for available data file prefixes"""
    prefixes: Dict[str, int] = Field(..., description="Map of file prefixes to counts")


class CategoryResponse(BaseModel):
    """Response for observation categories"""
    categories: List[str] = Field(..., description="List of available categories")
    counts: Dict[str, int] = Field(..., description="Map of categories to counts")
    total_files: int = Field(..., description="Total number of files processed")


class VitalResponse(BaseModel):
    """Response for vitals within a category"""
    category: str = Field(..., description="Category name")
    vitals: Dict[str, int] = Field(..., description="Map of vital names to counts")


class DataPoint(BaseModel):
    """Individual data point"""
    date: str = Field(..., description="Date in ISO format")
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit of measurement")
    name: str = Field(..., description="Name of the measurement")


class ObservationDataResponse(BaseModel):
    """Response for observation data"""
    category: str = Field(..., description="Category name")
    vital: str = Field(..., description="Vital sign name")
    data: List[DataPoint] = Field(..., description="List of data points")
    count: int = Field(..., description="Number of data points")


class ChartSeries(BaseModel):
    """Chart series data for ECharts"""
    name: str = Field(..., description="Series name")
    data: List[float] = Field(..., description="Data values")
    type: str = Field(default="line", description="Chart type")


class ChartDataResponse(BaseModel):
    """Response for chart data"""
    title: str = Field(..., description="Chart title")
    dates: List[str] = Field(..., description="X-axis dates")
    series: List[ChartSeries] = Field(..., description="Chart series data")
    chart_config: Dict[str, Any] = Field(..., description="Complete ECharts configuration")


class ConditionRecord(BaseModel):
    """Medical condition record"""
    resource_type: str = Field(..., description="Resource type")
    recorded_date: str = Field(..., description="Date recorded")
    clinical_status: str = Field(..., description="Clinical status code")
    verification_status: str = Field(..., description="Verification status code")
    condition_text: str = Field(..., description="Condition description")


class MedicationRecord(BaseModel):
    """Medication record"""
    resource_type: str = Field(..., description="Resource type")
    authored_date: str = Field(..., description="Date authored")
    status: str = Field(..., description="Medication status")
    medication_name: str = Field(..., description="Medication name")


class ProcedureRecord(BaseModel):
    """Procedure record"""
    resource_type: str = Field(..., description="Resource type") 
    performed_date: str = Field(..., description="Date performed")
    status: str = Field(..., description="Procedure status")
    procedure_text: str = Field(..., description="Procedure description")


class ConditionsResponse(BaseModel):
    """Response for conditions data"""
    conditions: List[ConditionRecord] = Field(..., description="List of conditions")
    count: int = Field(..., description="Number of conditions")


class MedicationsResponse(BaseModel):
    """Response for medications data"""
    medications: List[MedicationRecord] = Field(..., description="List of medications")
    count: int = Field(..., description="Number of medications")
    include_inactive: bool = Field(default=False, description="Whether inactive medications are included")


class ProceduresResponse(BaseModel):
    """Response for procedures data"""
    procedures: List[ProcedureRecord] = Field(..., description="List of procedures")
    count: int = Field(..., description="Number of procedures")


class FilterRequest(BaseModel):
    """Request model for data filtering"""
    after: Optional[str] = Field(None, description="Filter data after this date (YYYY-MM-DD)")
    before: Optional[str] = Field(None, description="Filter data before this date (YYYY-MM-DD)")
    format: str = Field(default="json", description="Response format (json, csv)")
    include_inactive: bool = Field(default=False, description="Include inactive records")