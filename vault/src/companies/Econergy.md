```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Econergy" or company = "Econergy")
sort location, dt_announce desc
```
