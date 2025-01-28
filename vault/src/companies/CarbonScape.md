```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "CarbonScape" or company = "CarbonScape")
sort location, dt_announce desc
```
