```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-01213-08715") and reject-phase = false
sort location, company asc
```
