```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-03956-09770") and reject-phase = false
sort location, company asc
```
