```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HRV-09137-09215") and reject-phase = false
sort location, company asc
```
