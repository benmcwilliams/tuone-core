```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ferrero" or company = "Ferrero")
sort location, dt_announce desc
```
