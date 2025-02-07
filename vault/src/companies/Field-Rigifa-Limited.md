```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Field-Rigifa-Limited" or company = "Field Rigifa Limited")
sort location, dt_announce desc
```
