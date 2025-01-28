```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Battery4Life" or company = "Battery4Life")
sort location, dt_announce desc
```
