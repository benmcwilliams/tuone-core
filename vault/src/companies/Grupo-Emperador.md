```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Grupo-Emperador" or company = "Grupo Emperador")
sort location, dt_announce desc
```
