```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Elering" or company = "Elering")
sort location, dt_announce desc
```
