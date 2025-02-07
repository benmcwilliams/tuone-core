```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Atlantique-Offshore-Energy" or company = "Atlantique Offshore Energy")
sort location, dt_announce desc
```
