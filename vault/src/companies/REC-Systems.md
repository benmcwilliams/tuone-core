```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "REC-Systems" or company = "REC Systems")
sort location, dt_announce desc
```
