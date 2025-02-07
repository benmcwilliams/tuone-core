```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "GRS" or company = "GRS")
sort location, dt_announce desc
```
