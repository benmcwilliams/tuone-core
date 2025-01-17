```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-10285-06411") and reject-phase = false
sort location, company asc
```
