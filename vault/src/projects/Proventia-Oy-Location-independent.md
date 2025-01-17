```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-09726-09797") and reject-phase = false
sort location, company asc
```
