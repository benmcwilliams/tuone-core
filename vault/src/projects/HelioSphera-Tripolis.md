```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GRC-09026-09127") and reject-phase = false
sort location, company asc
```
