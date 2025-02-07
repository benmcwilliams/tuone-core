```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Iceland-Resources-ehf." or company = "Iceland Resources ehf.")
sort location, dt_announce desc
```
