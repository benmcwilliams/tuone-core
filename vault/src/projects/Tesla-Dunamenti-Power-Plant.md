```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HUN-01965-00768") and reject-phase = false
sort location, company asc
```
