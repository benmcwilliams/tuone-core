```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "CGN-Europe-Energy" or company = "CGN Europe Energy")
sort location, dt_announce desc
```
