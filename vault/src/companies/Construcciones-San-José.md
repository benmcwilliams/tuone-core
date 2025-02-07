```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Construcciones-San-José" or company = "Construcciones San José")
sort location, dt_announce desc
```
