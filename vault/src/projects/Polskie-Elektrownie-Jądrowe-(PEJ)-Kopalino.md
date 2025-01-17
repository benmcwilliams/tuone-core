```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-09703-09760") and reject-phase = false
sort location, company asc
```
