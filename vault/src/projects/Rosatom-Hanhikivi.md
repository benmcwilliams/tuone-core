```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-09851-00672") and reject-phase = false
sort location, company asc
```
