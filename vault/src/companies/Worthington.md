```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Worthington" or company = "Worthington")
sort location, dt_announce desc
```
