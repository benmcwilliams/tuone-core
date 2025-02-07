```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Gresham-House" or company = "Gresham House")
sort location, dt_announce desc
```
