```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Greyp-Bikes" or company = "Greyp Bikes")
sort location, dt_announce desc
```
