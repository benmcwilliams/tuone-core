```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ternienergia-Spa" or company = "Ternienergia Spa")
sort location, dt_announce desc
```
