# UniPlanit

UniPlanit is a Python based scheduling system that processes university timetables and exports them to Excel.

Originally intended to track assignments with a monthly view, UniPlanit evolved into a fast timetable exporter due to
performance and native UI limitations for mobile with Kivy.

## Key Features

- Extraction of class details using an .ics URL link
- Automatic timetable clash detection
- Dynamic column insertion for clashing classes including several edge cases
- Preservation of cell styles during merges  
- Intelligent location string cleaning and parsing
- Extra GPA calculator application optimised for clean UI for both desktop and mobile

## Visual Comparison
![Timetable export comparison between UniPlanit and Allocate+](Timetable-Comparison.jpg)
| Feature / Aspect                  | Default Allocate+ Export           | UniPlanit Excel Export                     |
|----------------------------------|-----------------------------------|-------------------------------------------|
| **Location formatting**           | Long and hard to read, sometimes missing | Cleaned and standardised            |
| **Module grouping**               | Inconsistent visual grouping                | Colour coded by lectures and tutorials                     |
| **Printing / export**             | Cluttered, pdf cannot be modified                  | Optimised for print, easy editing in Excel          |


## Engineering Challenges Solved

- Designed a dictionary-based time-slot collision detection system
- Implemented dynamic Excel sheet mutation at runtime  
- Managed immutable style objects safely in `openpyxl`  
- Prevented partial merge conflicts during structural changes to prevent file corruption
- Maintained visual integrity under complex overlapping schedules

## Technologies Used

- Python  
- openpyxl library (for working with Excel)
- Regex
- Kivy / KivyMD (for UI development with mobile support)

## How to Run

```bash
pip install -r requirements.txt
python3 week-timetable.py
```