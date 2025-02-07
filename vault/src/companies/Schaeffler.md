```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Schaeffler" or company = "Schaeffler")
sort location, dt_announce desc
```
