```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SVN-10265-10419") and reject-phase = false
sort location, company asc
```
