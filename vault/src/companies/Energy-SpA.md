```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Energy-Spa" or company = "Energy Spa")
sort location, dt_announce desc
```
