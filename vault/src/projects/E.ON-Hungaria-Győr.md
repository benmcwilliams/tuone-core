```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HUN-00417-04848") and reject-phase = false
sort location, company asc
```
