```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-00386-01091") and reject-phase = false
sort location, company asc
```
