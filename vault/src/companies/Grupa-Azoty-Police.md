```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Grupa-Azoty-Police" or company = "Grupa Azoty Police")
sort location, dt_announce desc
```
