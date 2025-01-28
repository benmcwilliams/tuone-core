```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "INVL-Renewable-Energy-Fund-1" or company = "INVL Renewable Energy Fund 1")
sort location, dt_announce desc
```
