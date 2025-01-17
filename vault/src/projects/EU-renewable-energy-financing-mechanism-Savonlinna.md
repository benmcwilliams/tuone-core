```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-04424-04880") and reject-phase = false
sort location, company asc
```
