```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "P2-Solar" or company = "P2 Solar")
sort location, dt_announce desc
```
