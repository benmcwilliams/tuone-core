```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-01039-00767") and reject-phase = false
sort location, company asc
```
