```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-08084-08369") and reject-phase = false
sort location, company asc
```
