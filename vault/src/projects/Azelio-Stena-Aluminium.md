```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-01353-00932") and reject-phase = false
sort location, company asc
```
