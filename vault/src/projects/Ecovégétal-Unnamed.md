```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-03023-03912") and reject-phase = false
sort location, company asc
```
