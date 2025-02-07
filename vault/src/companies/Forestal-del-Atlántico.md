```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Forestal-del-Atlántico" or company = "Forestal del Atlántico")
sort location, dt_announce desc
```
