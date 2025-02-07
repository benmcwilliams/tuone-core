```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Axpo-Nordic" or company = "Axpo Nordic")
sort location, dt_announce desc
```
