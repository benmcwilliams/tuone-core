```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-08849-09754") and reject-phase = false
sort location, company asc
```
