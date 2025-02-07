```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Estonian-Geological-Service" or company = "Estonian Geological Service")
sort location, dt_announce desc
```
