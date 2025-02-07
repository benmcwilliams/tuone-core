```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solar-Frontier" or company = "Solar Frontier")
sort location, dt_announce desc
```
