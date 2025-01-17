```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-09422-07937") and reject-phase = false
sort location, company asc
```
