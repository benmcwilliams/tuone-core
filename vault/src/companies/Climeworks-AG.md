```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Climeworks-AG" or company = "Climeworks AG")
sort location, dt_announce desc
```
