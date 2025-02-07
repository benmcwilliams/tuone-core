```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Bventus" or company = "Bventus")
sort location, dt_announce desc
```
