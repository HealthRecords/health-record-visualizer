# Health Record Visualizer (HaRVey) - Project Structure

## Overview
HaRVey is a health record visualization application that processes Apple Health exports and medical records from providers like Kaiser Permanente. It supports both FHIR JSON files and CDA XML formats, providing interactive web-based charts and data exploration.

## Quick Start Context
- **Main Entry**: `python start_server.py` or `python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- **Web Interface**: http://localhost:8000
- **Configuration**: Edit `config.py` to set data path
- **Data Location**: Apple Health export directory with `clinical-records/` subdirectory

## Core Application Architecture

### Web Application (Primary Interface)
- **FastAPI Server**: `main.py` - Modern web interface with REST API endpoints
- **Server Startup**: `start_server.py` - Uvicorn server launcher with configuration
- **Legacy Flask**: `server.py` - Older Flask-based interface (deprecated)

### Data Processing Libraries
- **Core Library**: `health_lib.py` - Main data processing, FHIR JSON parsing
- **CDA Processing**: `health_lib_cda.py` - Clinical Document Architecture XML support
- **XML Reader**: `xml_reader.py` - Generic XML parsing utilities
- **Data Models**: `models.py` - Pydantic schemas for API responses

### Command Line Interface (Legacy)
- **CLI Main**: `health.py` - Command line health data explorer
- **Text UI**: `text_ui.py` - Interactive text-based menu system

### Configuration & Utilities
- **Configuration**: `config.py` - Data paths, database settings, utilities
- **Synthea Converter**: `convert_synthea.py` - Convert Synthea test data format
- **CDA Preprocessor**: `preprocess_cda.py` - XML to SQLite database converter
- **Tag Finder**: `find_tags.py` - XML structure discovery tool

## Data Processing Flow

### Input Data Formats
1. **Apple Health Export** (`clinical-records/*.json`)
   - FHIR R4 compliant JSON files
   - Types: Observation, Condition, MedicationRequest, Procedure, AllergyIntolerance
2. **CDA XML** (`export_cda.xml`)
   - Clinical Document Architecture format
   - Preprocessed into SQLite database (`cda_observations.db`)

### Visualization Libraries Supported
- **Apache ECharts** - Primary charting (interactive web charts)
- **Matplotlib** - Static chart generation (`plot_health.py`)
- **Pygal** - SVG charts
- **D3.js** - Custom visualizations (`d3_example.py`, `d3_template.html`)

## Directory Structure

```
health-record-visualizer/
├── main.py                    # FastAPI web application (PRIMARY)
├── start_server.py           # Server startup script
├── config.py                 # Configuration management
├── models.py                 # Pydantic data models
├── health_lib.py            # Core FHIR data processing
├── health_lib_cda.py        # CDA XML processing  
├── health.py                # CLI interface
├── text_ui.py               # Interactive CLI menu
├── server.py                # Legacy Flask server
├── xml_reader.py            # XML parsing utilities
├── preprocess_cda.py        # CDA-to-database converter
├── convert_synthea.py       # Synthea data converter
├── find_tags.py             # XML structure analyzer
├── plot_health.py           # Matplotlib plotting
├── d3_example.py            # D3.js chart generation
├── sparklines.py            # Sparkline charts
├── sparkbase.py             # Base sparkline functionality
│
├── templates/               # Jinja2 HTML templates
│   ├── index.html           # Homepage with navigation
│   ├── base.html            # Base template
│   ├── observations.html    # Observation categories
│   ├── vitals.html          # Vital signs list
│   ├── vital_detail.html    # Individual vital charts
│   ├── conditions.html      # Medical conditions
│   ├── medications.html     # Medications list
│   ├── procedures.html      # Medical procedures
│   ├── cda_*.html          # CDA-specific templates
│   └── generic_data.html    # Generic FHIR resource display
│
├── static/                  # Web assets
│   ├── css/custom.css       # Styling
│   ├── js/app.js           # Frontend JavaScript
│   ├── logo.svg            # Application logo
│   └── logo_small.svg      # Compact logo
│
├── test_data/              # Sample data for testing
│   ├── *.json              # Sample FHIR observations
│   ├── *.xml               # Sample CDA documents
│   └── list_prefixes_test_dir/
│
├── output/                 # Generated files
│   ├── sparkbase.html      # Generated sparkline charts
│   └── sparkbase_spo2.html
│
├── tests/                  # Test files
│   ├── test_health.py
│   ├── test_sparkbase.py
│   └── test_xml_reader.py
│
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project metadata
├── README.md              # Documentation
└── _TODOs.md             # Development tasks
```

## Key API Endpoints (main.py)

### Core Navigation
- `GET /` - Homepage with data summary
- `GET /observations` - Observation categories
- `GET /observations/{category}` - Vitals in category  
- `GET /observations/{category}/{vital}` - Individual vital detail

### Medical Records  
- `GET /conditions` - Medical conditions
- `GET /medications` - Prescription medications
- `GET /procedures` - Medical procedures
- `GET /allergies` - Allergy information

### Data APIs
- `GET /api/observations/{category}/{vital}/data` - Raw data with filtering
- `GET /api/observations/{category}/{vital}/chart` - ECharts configuration
- `GET /api/conditions`, `/api/medications`, `/api/procedures` - Medical record data

### CDA Support
- `GET /cda` - CDA data overview
- `GET /cda/{category}` - CDA category (Vital Signs, Laboratory)
- `GET /api/cda/{category}/{observation}/chart` - CDA charting with bucketing

## Development Context

### Data Source Configuration
```python
# config.py - Key settings
source_dir = Path("/path/to/apple_health_export")  # Main data directory
# Environment variable: HEALTH_DATA_DIR overrides config.py
```

### Key Dependencies
- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation and serialization  
- **Jinja2** - HTML templating
- **Matplotlib/Pygal** - Chart generation
- **SQLite3** - CDA data storage
- **BeautifulSoup** - XML parsing

### Testing
- `python -m unittest discover` - Run all tests
- Test data in `test_data/` directory
- Unit tests for core libraries

### Chart Features
- **Time Series**: Interactive line charts for vital signs
- **Reference Ranges**: Normal lab value highlighting
- **Multi-value Support**: Blood pressure (systolic/diastolic)
- **Date Filtering**: Time range selection
- **Export Options**: CSV/JSON data download
- **Data Bucketing**: Automatic aggregation for large datasets

### Common Development Tasks
1. **Adding New Data Types**: Extend `main.py` endpoints and `models.py` schemas
2. **Chart Customization**: Modify ECharts configurations in chart endpoints
3. **Template Updates**: Edit HTML templates in `templates/`
4. **Data Processing**: Extend `health_lib.py` for new FHIR resources

### Debugging
- **Debug Mode**: `python start_server.py --reload`  
- **Logs**: Check `app.log` for errors
- **Data Issues**: Verify `clinical-records/` directory exists and has permissions

## Performance Notes
- **Large Datasets**: CDA processing uses SQLite with bucketing (hourly/daily/monthly aggregation)
- **Chart Optimization**: Automatic data point reduction for better rendering
- **Memory**: Processes data incrementally, not all in memory

This structure provides the essential context needed to quickly understand and work with the HaRVey health record visualization system in future sessions.