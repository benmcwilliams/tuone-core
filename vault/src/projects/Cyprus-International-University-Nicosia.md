```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "CYP-08365-08580") and reject-phase = false
sort location, company asc
```
