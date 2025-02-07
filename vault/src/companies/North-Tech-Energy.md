```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "North-Tech-Energy" or company = "North Tech Energy")
sort location, dt_announce desc
```
