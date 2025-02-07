```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Capital-Stage" or company = "Capital Stage")
sort location, dt_announce desc
```
