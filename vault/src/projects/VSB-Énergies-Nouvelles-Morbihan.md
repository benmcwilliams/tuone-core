```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-06013-06679") and reject-phase = false
sort location, company asc
```
