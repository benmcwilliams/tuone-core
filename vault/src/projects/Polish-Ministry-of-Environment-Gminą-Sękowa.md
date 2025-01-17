```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-09171-09755") and reject-phase = false
sort location, company asc
```
