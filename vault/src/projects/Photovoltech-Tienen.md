```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BEL-09693-09743") and reject-phase = false
sort location, company asc
```
