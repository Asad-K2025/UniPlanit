import requests
from ics import Calendar

url = input('Paste your ical url for your timetable: ')
request = requests.get(url)
calendar = Calendar(request.text)

for event in calendar.events:
    print(f"{event.name} – {event.begin.date()} at {event.begin.time()}")

