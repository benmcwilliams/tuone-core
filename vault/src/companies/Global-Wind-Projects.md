```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Global-Wind-Projects" or company = "Global Wind Projects")
sort location, dt_announce desc
```
