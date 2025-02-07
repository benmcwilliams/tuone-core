```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Supersteel" or company = "Supersteel")
sort location, dt_announce desc
```
