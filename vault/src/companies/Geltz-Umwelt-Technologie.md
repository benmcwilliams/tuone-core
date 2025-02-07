```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Geltz-Umwelt-Technologie" or company = "Geltz Umwelt Technologie")
sort location, dt_announce desc
```
