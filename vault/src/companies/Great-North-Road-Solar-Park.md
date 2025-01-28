```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Great-North-Road-Solar-Park" or company = "Great North Road Solar Park")
sort location, dt_announce desc
```
