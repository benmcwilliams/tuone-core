```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CHE-04748-05160") and reject-phase = false
sort location, company asc
```
