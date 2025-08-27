# TODOs

1. Sparklines don't need to be zero based, 
3. http://localhost:8000/observations/laboratory/MULTIPLE%20MYELOMA%20PROGNOSIS%20PANEL%2C%20FISH%2C%20REPORT
   4. Doesn't work right now. I can't find the note in the results, yet. 
   5. Needs a "view raw" option

# Tests
Needs more tests.

# Notes
Things that may not require action, at least on my end.

 1. I don't currently handle the difference between < and <= on reference ranges. Is there really a difference?
 1. Some data appears to be missing from my download (PSA). 
    1. There are two versions of the test in my original medical record, with the same name. 
    2. I suspect they got incorrectly de-duped along the way. maybe something non-unique was put into a dict representation
