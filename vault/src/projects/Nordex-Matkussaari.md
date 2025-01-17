```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-09487-07472") and reject-phase = false
sort location, company asc
```
