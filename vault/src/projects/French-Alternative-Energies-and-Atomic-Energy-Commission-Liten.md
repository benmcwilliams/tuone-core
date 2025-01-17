```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-07348-07799") and reject-phase = false
sort location, company asc
```
