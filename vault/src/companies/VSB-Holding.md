```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "VSB-Holding" or company = "VSB Holding")
sort location, dt_announce desc
```
