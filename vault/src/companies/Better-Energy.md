```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Better-Energy" or company = "Better Energy")
sort location, dt_announce desc
```
