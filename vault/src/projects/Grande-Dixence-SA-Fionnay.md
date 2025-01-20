```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "CHE-08927-09046") and reject-phase = false
sort location, company asc
```
