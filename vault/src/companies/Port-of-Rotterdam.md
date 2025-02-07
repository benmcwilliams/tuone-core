```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Port-of-Rotterdam" or company = "Port of Rotterdam")
sort location, dt_announce desc
```
