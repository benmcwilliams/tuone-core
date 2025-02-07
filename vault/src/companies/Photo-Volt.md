```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Photo-Volt" or company = "Photo Volt")
sort location, dt_announce desc
```
