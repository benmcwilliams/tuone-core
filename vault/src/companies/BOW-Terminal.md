```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "BOW-Terminal" or company = "BOW Terminal")
sort location, dt_announce desc
```
