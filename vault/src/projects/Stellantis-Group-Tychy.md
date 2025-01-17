```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-01149-02453") and reject-phase = false
sort location, company asc
```
