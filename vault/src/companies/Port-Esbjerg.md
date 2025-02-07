```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Port-Esbjerg" or company = "Port Esbjerg")
sort location, dt_announce desc
```
