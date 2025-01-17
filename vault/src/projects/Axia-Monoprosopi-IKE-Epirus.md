```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GRC-08035-04549") and reject-phase = false
sort location, company asc
```
