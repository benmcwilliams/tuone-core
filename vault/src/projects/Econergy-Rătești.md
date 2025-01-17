```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ROU-08510-04896") and reject-phase = false
sort location, company asc
```
