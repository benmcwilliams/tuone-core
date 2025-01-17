```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "EST-08242-08468") and reject-phase = false
sort location, company asc
```
