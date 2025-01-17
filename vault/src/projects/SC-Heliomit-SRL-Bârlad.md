```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ROU-09859-09892") and reject-phase = false
sort location, company asc
```
