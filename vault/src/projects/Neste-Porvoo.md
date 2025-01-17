```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-05234-05658") and reject-phase = false
sort location, company asc
```
