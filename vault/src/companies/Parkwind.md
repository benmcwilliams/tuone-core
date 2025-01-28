```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Parkwind" or company = "Parkwind")
sort location, dt_announce desc
```
