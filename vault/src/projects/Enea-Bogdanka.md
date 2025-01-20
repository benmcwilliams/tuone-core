```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "POL-08580-06476") and reject-phase = false
sort location, company asc
```
