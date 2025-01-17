```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-01127-00280") and reject-phase = false
sort location, company asc
```
