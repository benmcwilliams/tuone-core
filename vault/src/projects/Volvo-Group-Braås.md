```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-05563-00846") and reject-phase = false
sort location, company asc
```
