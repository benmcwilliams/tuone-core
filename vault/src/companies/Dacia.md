```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Dacia" or company = "Dacia")
sort location, dt_announce desc
```
