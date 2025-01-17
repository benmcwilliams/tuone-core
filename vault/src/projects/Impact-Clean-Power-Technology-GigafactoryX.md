```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-00379-00383") and reject-phase = false
sort location, company asc
```
