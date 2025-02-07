```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Wind-Power-Lab" or company = "Wind Power Lab")
sort location, dt_announce desc
```
