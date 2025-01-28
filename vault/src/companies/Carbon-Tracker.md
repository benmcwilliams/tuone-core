```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Carbon-Tracker" or company = "Carbon Tracker")
sort location, dt_announce desc
```
