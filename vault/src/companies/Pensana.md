```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Pensana" or company = "Pensana")
sort location, dt_announce desc
```
