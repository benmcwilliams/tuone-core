```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "VBMS" or company = "VBMS")
sort location, dt_announce desc
```
