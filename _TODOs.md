

# TODOs

## Simplify setup
Update proprocess_cda.py and propreocess_apple.py to use the value of _source_dir in config.py as a default 
   Fixed: preprocess_cda.py

Fix the setup in readme to run a script that does all the preprocessing and uses the setting in config.py

## Card Paths
The static cards are apparently all different on different paths. 
	modified:   templates/apple_record.html
	modified:   templates/cda_observation.html
	modified:   templates/vital_detail.html
Had to change all three to get coverage. and "Vital Detail" sounds suspicious.

## Combine graphs
we should be able to put two statics on one graph. Do this when I need it.

## Unique IDs for statistics.
When we have one statistic in two places, it should show on one graph.
we need to use a standard ID, not the text description, to select statistics. This avoids the whole case-sensitivity issue.
case sensitivity is explictly F@#$ in the spec. It depends on the source, who doesn't tell you. 
all of the above are related. 

we have an issue for this: https://github.com/HealthRecords/health-record-visualizer/issues/10

related:
Different labs produce different results. They also may report in different units. Need to differentiate by source, and
make sure units are consistent. Should we have a separate entry per source? Probably.

## Misc

http://localhost:8000/cda/vital-signs/Oxygen%20saturation


1. Sparklines don't need to be zero based,  (later: what?)

3. http://localhost:8000/observations/laboratory/MULTIPLE%20MYELOMA%20PROGNOSIS%20PANEL%2C%20FISH%2C%20REPORT
   4. Doesn't work right now. I can't find the note in the results, yet. 
   5. Needs a "view raw" option

# Tests
Needs more tests.

# Notes
Things that may not require action, at least on my end.

fix favicons on http://localhost:8000/cda/biometrics/Body%20weight%20Measured, it's not all the time, but on the console log, when going
back and forth, I get a 404 for favion.ico

if you zoom into or out of a chart with two fingers, it doesn't update the bucket size, so the stats don't change. I'm not certain this is a problem

 1. Should vital signs and test names be case-insensitive?
2. I don't currently handle the difference between < and <= on reference ranges. Is there really a difference?

 1. Some data appears to be missing from my download (PSA). 
    1. There are two versions of the test in my original medical record, with the same name. 
    2. I suspect they got incorrectly de-duped along the way. maybe something non-unique was put into a dict representation


to run sparkbase:
 python sparkbase.py --apple --days --file output/sparkbase_spo2.html --cat "Oxygen saturation" --device "EMAY Oximeter" --after 2024-01-01
 
Need to integrate sparkbase into webapp


