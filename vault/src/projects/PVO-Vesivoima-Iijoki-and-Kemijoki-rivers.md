```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-09656-09698") and reject-phase = false
sort location, company asc
```
