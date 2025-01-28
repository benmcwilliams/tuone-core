```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sunly" or company = "Sunly")
sort location, dt_announce desc
```
