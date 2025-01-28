```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "National-Highways" or company = "National Highways")
sort location, dt_announce desc
```
