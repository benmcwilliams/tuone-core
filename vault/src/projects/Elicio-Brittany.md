```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-06218-07727") and reject-phase = false
sort location, company asc
```
