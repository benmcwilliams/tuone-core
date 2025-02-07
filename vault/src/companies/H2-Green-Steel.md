```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "H2-Green-Steel" or company = "H2 Green Steel")
sort location, dt_announce desc
```
