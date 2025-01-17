```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-09145-05351") and reject-phase = false
sort location, company asc
```
