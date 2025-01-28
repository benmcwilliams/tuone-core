```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Port-Oostende" or company = "Port Oostende")
sort location, dt_announce desc
```
