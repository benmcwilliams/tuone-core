```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "BayWar.e.-Wind" or company = "BayWar.e. Wind")
sort location, dt_announce desc
```
