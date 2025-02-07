```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Xinte" or company = "Xinte")
sort location, dt_announce desc
```
