```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "AUT-01420-01037") and reject-phase = false
sort location, company asc
```
