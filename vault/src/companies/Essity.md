```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Essity" or company = "Essity")
sort location, dt_announce desc
```
