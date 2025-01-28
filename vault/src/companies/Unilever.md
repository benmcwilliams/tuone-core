```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Unilever" or company = "Unilever")
sort location, dt_announce desc
```
