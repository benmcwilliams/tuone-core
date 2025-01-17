```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GRC-06024-01789") and reject-phase = false
sort location, company asc
```
