```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "European-Energy" or company = "European Energy")
sort location, dt_announce desc
```
