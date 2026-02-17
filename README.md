# UniPlanit

UniPlanit is a Python based scheduling system that processes university timetables and exports them to Excel.

## Key Features

- Extraction of class details using an .ics URL link
- Automatic timetable clash detection
- Dynamic column insertion for clashing classes including several edge cases
- Preservation of cell styles during merges  
- Intelligent location string cleaning and parsing
- Extra GPA calculator application optimised for clean UI for both desktop and mobile

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

Ins
```bash
pip install -r requirements.txt
python3 week-timetable.py
```