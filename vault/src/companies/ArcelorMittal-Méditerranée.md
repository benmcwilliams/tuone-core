```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "ArcelorMittal Méditerranée"
sort location, dt_announce desc
```
