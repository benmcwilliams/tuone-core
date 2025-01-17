```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-05055-06476") and reject-phase = false
sort location, company asc
```
