# https://github.com/codingforentrepreneurs/Pi-Awesome/blob/main/how-tos/Create%20a%20Minimal%20Web%20Application%20with%20Nginx%2C%20Python%2C%20Flask%20%26%20Raspberry%20Pi.md
import os

from flask import Flask, render_template
import logging

import config
from health_lib import list_prefixes

# Configuration for logging
logging.basicConfig(
    filename='app.log',  # Specify your log file name
    level=logging.ERROR,  # Set the logging level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Format of the log messages
)

app = Flask(__name__)
@app.route('/clinical')
def serve_clinical():
    try:
        # Set the path to the directory where you have expanded the apple health export file
        # export_path = Path('/Users/tomhill/Downloads/AppleHealth/apple_health_export')
        export_path = config.source_dir
        assert os.path.exists("templates/index.html")
        observation_path = condition_path = export_path / "clinical-records"
        options = list(list_prefixes(observation_path).keys())
        o1 = {option:option for option in options}
        return render_template('index.html', urls=options, back="/")
    except Exception as e:
        logging.exception(e)
        return "An error occurred: "+e, 500


@app.route('/')
def hello_world():
    return render_template('index.html', urls={'Clinical': "clinical", 'export.xml':"export", 'export_cda.xml':"cda"}, back="/")



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8123)
