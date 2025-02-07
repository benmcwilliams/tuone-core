```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Envie-2E-Aquitaine" or company = "Envie 2E Aquitaine")
sort location, dt_announce desc
```
