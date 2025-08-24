# Health Data Explorer - Apple Health & Medical Records Visualizer

This application provides a modern web interface for exploring Apple Health exports and medical records data. It features interactive charts, data filtering, and comprehensive visualization of your health data.

## Disclaimer

**This software is for informational purposes only and is not intended for medical decision-making. Always consult with healthcare professionals for medical advice. The authors are not responsible for any medical decisions made based on this software's output.**

![Health Data Explorer](screenshot_delete_me.png)

## Features

- **Web-based Interface**: Modern, responsive Bootstrap 5 UI
- **Interactive Charts**: Apache ECharts integration with reference range visualization
- **Medical Records Support**: View conditions, medications, procedures, and lab results
- **Data Filtering**: Filter by date ranges and other criteria
- **Reference Ranges**: Automatic display of normal lab value ranges
- **Export Options**: Export data as CSV or JSON
- **Multi-value Observations**: Support for complex readings like blood pressure
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Apple Health export data (see [Getting Your Data](#getting-your-data) below)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tomhill/HealthDataApple.git
   cd HealthDataApple
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   python -m pip install -r requirements.txt
   ```

4. **Configure your data path:**
   
   Edit `config.py` and update the `source_dir` path to point to your Apple Health export:
   ```python
   from pathlib import Path
   source_dir = Path("/path/to/your/apple_health_export")
   ```

5. **Start the server:**
   ```bash
   # Option 1: Using the startup script (recommended)
   python start_server.py
   
   # Option 2: Direct uvicorn command
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Open your browser:**
   
   Navigate to http://localhost:8000

## Getting Your Data

### From Kaiser Permanente (via Apple Health)

1. Open the **Apple Health** app on your iPhone
2. Tap your **profile picture** to open your profile
3. Select **"Health Records"** → **"Add Accounts"**
4. Follow prompts to connect Kaiser Permanente
5. Return to profile and select **"Export All Health Data"**
6. Wait for processing (may take several minutes)
7. Save/AirDrop the export to your computer
8. Unzip the export file

### Directory Structure

After unzipping, you'll have:
```
apple_health_export/
├── clinical-records/          # Medical records (JSON files)
│   ├── Observation-*.json     # Lab results, vitals
│   ├── Condition-*.json       # Diagnoses
│   ├── MedicationRequest-*.json
│   └── Procedure-*.json
├── export.xml                 # Apple Health data
├── export_cda.xml            # Additional health data
└── workout-routes/           # GPS workout data
```

## Usage

### Web Interface

The web interface provides several main sections:

- **Observations**: Lab results and vital signs with interactive charts
- **Conditions**: Medical diagnoses and health conditions  
- **Medications**: Prescription medications and requests
- **Procedures**: Medical procedures and treatments

### Chart Features

- **Time Series Visualization**: View trends over time
- **Reference Ranges**: Normal lab value ranges displayed as background bands
- **Multi-value Support**: Blood pressure, etc. with separate series for each value
- **Interactive Tooltips**: Hover for detailed information
- **Date Filtering**: Focus on specific time periods
- **Export Options**: Download chart data as CSV/JSON

### Command Line Interface (Legacy)

For command-line usage:

```bash
# Interactive menu
python text_ui.py

# Direct commands
python health.py --stat "Blood Pressure" --plot --after 2024-01-01
python health.py --help
```

## Development

### Project Structure

```
HealthDataApple/
├── main.py              # FastAPI application
├── models.py            # Pydantic data models
├── health_lib.py        # Core data processing
├── config.py            # Configuration settings
├── templates/           # Jinja2 HTML templates
├── static/              # CSS, JavaScript assets
└── requirements.txt     # Python dependencies
```

### Development Setup

1. Install development dependencies:
   ```bash
   python -m pip install -e ".[dev]"
   ```

2. Run with auto-reload:
   ```bash
   python start_server.py --reload
   ```

3. Run tests:
   ```bash
   pytest
   ```

### Adding New Features

The application is designed to be extensible:

- **New data types**: Add endpoints in `main.py` and models in `models.py`
- **Chart types**: Extend ECharts configuration in chart endpoints
- **UI components**: Add templates and update navigation

## Configuration

### Environment Variables

Set these in your environment or `.env` file:

```bash
HEALTH_DATA_PATH=/path/to/apple_health_export
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false
```

### config.py Settings

```python
from pathlib import Path

# Path to your Apple Health export directory
source_dir = Path("/path/to/your/apple_health_export")

# Optional: Custom settings
DEFAULT_ITEMS_PER_PAGE = 50
CHART_HEIGHT = 400
```

## Troubleshooting

### Common Issues

**"No data found"**: 
- Verify `config.py` points to correct export directory
- Ensure `clinical-records/` subdirectory exists
- Check file permissions

**Import errors**:
- Activate virtual environment: `source .venv/bin/activate`
- Install requirements: `python -m pip install -r requirements.txt`

**Charts not loading**:
- Check browser console for JavaScript errors
- Verify ECharts CDN is accessible
- Try refreshing the page

### Debugging

Enable debug mode in `start_server.py`:
```bash
python start_server.py --reload
```

Check logs in `app.log` for detailed error information.

## Data Privacy & Security

**Important**: This application processes sensitive health data:

- **Local Processing**: All data processing happens locally on your machine
- **No Remote Access**: No data is sent to external servers
- **File Permissions**: Ensure proper file system permissions
- **Network Access**: Server only binds to localhost by default

## Alternatives

If you need more polished or supported solutions:

- [Fasten Health](https://www.fastenhealth.com/) - Open source personal health record
- [Mere Medical](https://meremedical.co/) - Personal health data platform
- [OpenMHealth](https://www.openmhealth.org/) - Open mobile health toolkit

## Data Format Notes

This tool works with:
- **FHIR R4** medical records (JSON format)
- **Apple Health** export formats (XML/JSON)
- **Kaiser Permanente** exports (via Apple Health)
- Other healthcare providers using standard FHIR formats

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

Apache 2.0 License - see [LICENSE](LICENSE) file for details.