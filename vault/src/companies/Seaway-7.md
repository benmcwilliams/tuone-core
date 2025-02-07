```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Seaway-7" or company = "Seaway 7")
sort location, dt_announce desc
```
