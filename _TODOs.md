# TODOs



Consolidating top-of-file TODOs I had been using, when this was one file, now that it is several files.

With a single developer, a bug tracker is too heavyweight.

# Simple
1. handle non-numeric response. I know the creatine one has this, and http://localhost:8000/observations/lab/AB%20screen%2C%20blood looks like it too. 
2. Update references, etc, so others can install and run.
3. When plotting, we should not always write to the same file, and we should tell the user where we wrote the plot.
files are hard coded, should pass them in.both the above and the source file(s) - are there any places that do this left?
4. Add a smoothing option to the charts, it's hard to read when it jumps around a lot.
5. on the blood pressure graph, we still have numeric labels on each point on diastolic. We already removed them from 
systolic (and everything else)
6. write all graphs to "output" folder. 
7. get ready for pypi, move all .py files to a package.
8. Fails to plot 

#  Architecture
1. Switch to apache echarts to get interactive charts. 
   2. Mostly done. Sparklines still use matplotlib.
2. Split this file into UI code, and library code. We already have text_ui, and xml_reader which use this file.
       Should be able to pass in an output function (print, plot with matplotlib, generate html page, etc.)
   2. Basic split has been done. Still some things to be moved around for the full UI/data access split
1. Maybe a second functional split. UIs that print, text_ui, health.py, share common code. 
1. Where does 'plot' belong? A third module, which is pluggable 
   1. Should be able to pass in an output function (print, plot with matplotlib, generate html page, etc.)
 1.  There should be a generic interface for plotting, so I can replace it.
    That might be hard to do, if some are plotting locally, some are saving to a static html file, and some are in django
1. Should be able to graph anything with a value quantity and a date. This is only observations, at least
      in my data. Need to handle string values for Observations
 1. I have D3 plotting code, but the HTML page needs to be different, since we have to include a lot of JS.
2. print_condition and print_medicines should be generalized and combined.
 1. Do we want to have an option to process multiple or all stats in one run?
 1. When getting multiple stats, I reread ALL the observation files for each stat. Optimize.
 1. Check single ended string referenceRanges, like "<50". How well does that graph? I treat this as
       -sys.maxsize < X < 50
 1. What about single valueQuantities that represent a range, with a "value" : 60,
        and a "comparator"  of ">". So far, I have only seen this is a single value, not a range. Skip for now.
1. Not sure if "do_vitals" belongs ion health.py, or in health_lib.py. Probably needs to be refactored
1Need to include data from xml_reader.py into sparklines
1. Sparklines don't need to be zero based, 
2. Open the zip file directly, expanding takes space, and is likely slower,
3. http://localhost:8000/observations/laboratory/MULTIPLE%20MYELOMA%20PROGNOSIS%20PANEL%2C%20FISH%2C%20REPORT
   4. Doesn't work right now. I can't find the note in the results, yet. 

# Tests
Needs more tests.

# Concepts
1. How should I plot values (not ranges) that are expressed as "60" with a comparator of ">". 
   1. "CREATININE AND CALCULATED GLOMERULAR FILTRATION RATE"
   2. It's not a point, which is what I expect. 
   3. I can't even figure out how this is stored, right now, if I search for 
   4. 
   5. "rg -l "CALCULATED GLOMERULAR FILTRATION RATE"
   6. I get lots of files, but the ones that i checked don't have the <60 that is displayed in the kaiser app.
   7. There are TWO files that have >60 in them. the rg above finds 586 files.

# Notes
Things that may not require action, at least on my end.

 1. I don't currently handle the difference between < and <= on reference ranges. Is there really a difference?
 1. Some data appears to be missing from my download (PSA). 
    1. There are two versions of the test in my original medical record, with the same name. 
    2. I suspect they got incorrectly de-duped along the way. maybe something non-unique was put into a dict representation
