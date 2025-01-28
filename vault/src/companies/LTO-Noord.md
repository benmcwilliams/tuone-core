```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "LTO-Noord" or company = "LTO Noord")
sort location, dt_announce desc
```
