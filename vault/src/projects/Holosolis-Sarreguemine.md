```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-07417-03008") and reject-phase = false
sort location, company asc
```
