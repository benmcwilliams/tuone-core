```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "POL-01149-10475") and reject-phase = false
sort location, company asc
```
