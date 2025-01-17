```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-08631-07746") and reject-phase = false
sort location, company asc
```
