```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Seaway-Heavy-Lifting" or company = "Seaway Heavy Lifting")
sort location, dt_announce desc
```
