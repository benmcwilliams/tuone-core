```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Strategic-Power-Projects" or company = "Strategic Power Projects")
sort location, dt_announce desc
```
