```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-00386-09039") and reject-phase = false
sort location, company asc
```
