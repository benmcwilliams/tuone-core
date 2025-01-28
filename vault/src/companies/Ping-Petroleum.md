```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ping-Petroleum" or company = "Ping Petroleum")
sort location, dt_announce desc
```
