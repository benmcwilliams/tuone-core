```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Port-Training-Services" or company = "Port Training Services")
sort location, dt_announce desc
```
