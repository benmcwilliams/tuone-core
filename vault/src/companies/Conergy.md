```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Conergy" or company = "Conergy")
sort location, dt_announce desc
```
