```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "PRT-07316-07778") and reject-phase = false
sort location, company asc
```
