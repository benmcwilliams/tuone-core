```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "3Flash" or company = "3Flash")
sort location, dt_announce desc
```
