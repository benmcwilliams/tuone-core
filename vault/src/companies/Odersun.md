```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Odersun" or company = "Odersun")
sort location, dt_announce desc
```
