```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "AUT-09372-09467") and reject-phase = false
sort location, company asc
```
