```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Mercedes-Benz" or company = "Mercedes Benz")
sort location, dt_announce desc
```
