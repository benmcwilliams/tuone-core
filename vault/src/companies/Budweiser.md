```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Budweiser" or company = "Budweiser")
sort location, dt_announce desc
```
