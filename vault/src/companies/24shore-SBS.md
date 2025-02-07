```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "24shore-SBS" or company = "24shore SBS")
sort location, dt_announce desc
```
