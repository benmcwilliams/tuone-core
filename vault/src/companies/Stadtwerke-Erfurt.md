```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Stadtwerke-Erfurt" or company = "Stadtwerke Erfurt")
sort location, dt_announce desc
```
