```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Star-Renewable-Energy" or company = "Star Renewable Energy")
sort location, dt_announce desc
```
