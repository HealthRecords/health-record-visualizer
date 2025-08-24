# Access Kaiser Health Data via iPhone and Apple Health

This repository shows how I am exploring my downloaded Apple Health and Kaiser medical record data. 

## Disclaimer
I am not medically trained, and have no documentation on the file format. This code is NOT for making medical decisions. There may be missing data and actual errors. I recommend discussing anything interesting you find with your doctor.

## Why?
My original goal was simply to chart my weight and blood pressure over time. Kaiser’s app can generate graphs of lab test results, but I haven’t found any way to graph vital signs. You can view each vital sign entry individually, but that’s not very useful.

This tool fills that gap: it can graph any Kaiser “Vital Sign” (such as weight) and also handle readings with two values per entry, like blood pressure (e.g., 120/90). In addition, it can print or graph test results, or anything else in the export with a recognizable format for values.

# How to Get Your Kaiser Medical Record data

1. What I did was go to the Apple Health app on my iPhone. 
2. Selected my profile picture to open my profile. 
2. Select "Health Records". "Add Accounts", and follow the prompts to add Kaiser.
3. The go back to the profile and select "Export All Data". This exports ALL your Apple Health data. So you not only get Kaiser medical records, but all records from Apple Health, including frequent updates from  your apple watch! The process took a couple of minutes. My health data was about 50MB, with an earliest record in 2007.  I assume that's when Kaiser went digital, since it's long before any other Apple Health data.
4. For me, it offered an airdrop option to my mac, but you can save it to files, I think, and move it where you want from there.
5. What you get is a single zip file. When you expand it, you get a large (1GB in my case) directory of files. 
6. It looks like all of the Kaiser files are json, in the clinical-records directory.
7. The Apple watch and other data from the iPhone are in export_cda.xml. This includes things that other devices write to 
   Apple Health.
1. I haven't gotten to export.xml yet.
6. Explore!

All of the above should be possible without an iPhone, but that's how I did it.

I'm using Kaiser Northern California. I believe this will work with other Kaiser groups, but I have not tested it. 

I believe this data format may be a [standard format](https://www.healthit.gov/faq/what-are-differences-between-electronic-medical-records-electronic-health-records-and-personal), so this code may work with more than just Kaiser.

# Files
When I expand the zip I get this directory structure:

```
./apple_health_export
./apple_health_export/workout-routes
./apple_health_export/clinical-records
./apple_health_export/electrocardiograms
```
Kaiser and presumably other third party provider's data is in .json files
in the clinical-records directory. I have seen this being thousands of files.
Each time the check your blood pressure, or weight, that's a separate file.

The Apple Health data is in the files export.xml and export_cda.xml files.
This may have hundreds of thousands of records, or probably more. 

Currently, the fastest way to explore this is the run the text_ui.py 
command line tool, as it examines the directories to see what files exist. 


# Running the Code
## Web UI (recommended)
The directory is currently hard coded in config.py, change it to point to your data directory.

To start the server:
```
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Then open this url in your browser:
```
http://localhost:8000
```

## Text UI
If you want to use this from the command line, here are some examples. This project started as a command line tool,
and we just added a web ui. The web UI is probably a better approach. 

The directory is currently hard coded in config.py, change it to point to your data directory.

I am using python 3.12.2

## For Kaiser / Medical items.
```python health.py --help```

```python health.py --stat Weight --print```

```python health.py --stat "Blood Pressure" --plot --after 2024-01-01```

## text_ui gives a simple, menu based command line tool
```python text_ui```

## Plot a statistic/test result
```
/Users/tomhill/PycharmProjects/HealthDataApple/health.py -s "Blood Pressure" --plot --print --after 2023-01-01 -l --source /Users/tomhill/Downloads/apple_health_export
```

## Look at Apple Health data. 
This tools is just getting started, today.
```python xml-reader --help```


# Alternatives
This is a weekend project, not a product. You are welcome to use it, and feedback is welcome. It's sweet spot is probably just
describing and giving example code for people who want to hack their own medical data. 

If you want a more polished or supported alternative, you might want to look at

1. Fasten Heath https://www.fastenhealth.com/
2. Mere Medical https://meremedical.co/


## Another Alternative
I'm not using this yet, just keeping track of this toolkit for later. https://www.openmhealth.org/

## Useful note:
[jq](https://jqlang.github.io/jq/) can be useful for exploring the data. For example, the following finds
unique values for referenceRange when only text, not high or low, is present. 
This helps me determine what I have to parse. The "-c" puts the json found all
on one line, so I can grep the result.

```jq -c -r '.referenceRange' O*.json | grep -v null  | grep -v low ```

All text in referenceRanges:

```jq -c -r '.referenceRange[].text' O*.json   | grep -v error | sort | uniq```
