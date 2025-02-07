```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "First-Subsea" or company = "First Subsea")
sort location, dt_announce desc
```
