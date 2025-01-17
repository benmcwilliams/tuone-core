```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-09591-09659") and reject-phase = false
sort location, company asc
```
