```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ISL-09262-04072") and reject-phase = false
sort location, company asc
```
