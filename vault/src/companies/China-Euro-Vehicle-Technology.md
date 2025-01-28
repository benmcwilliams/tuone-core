```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "China-Euro-Vehicle-Technology" or company = "China Euro Vehicle Technology")
sort location, dt_announce desc
```
