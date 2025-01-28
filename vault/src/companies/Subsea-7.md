```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Subsea-7" or company = "Subsea 7")
sort location, dt_announce desc
```
