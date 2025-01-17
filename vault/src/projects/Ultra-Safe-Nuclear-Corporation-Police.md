```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-08975-10277") and reject-phase = false
sort location, company asc
```
