```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "University-of-Applied-Sciences-and-Arts-of-Southern-Switzerland" or company = "University of Applied Sciences and Arts of Southern Switzerland")
sort location, dt_announce desc
```
