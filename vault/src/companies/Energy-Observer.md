```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Energy-Observer" or company = "Energy Observer")
sort location, dt_announce desc
```
