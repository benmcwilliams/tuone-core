```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-09940-07158") and reject-phase = false
sort location, company asc
```
