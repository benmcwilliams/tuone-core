```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "University-of-Surrey" or company = "University of Surrey")
sort location, dt_announce desc
```
