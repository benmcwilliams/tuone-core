```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Nowega" or company = "Nowega")
sort location, dt_announce desc
```
