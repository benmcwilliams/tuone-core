```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-02914-03087") and reject-phase = false
sort location, company asc
```
