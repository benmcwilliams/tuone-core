```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-09899-09930") and reject-phase = false
sort location, company asc
```
