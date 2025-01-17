```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SVK-09661-09700") and reject-phase = false
sort location, company asc
```
