```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Axter" or company = "Axter")
sort location, dt_announce desc
```
