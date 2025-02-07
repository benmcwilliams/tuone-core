```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Port-of-Amsterdam" or company = "Port of Amsterdam")
sort location, dt_announce desc
```
