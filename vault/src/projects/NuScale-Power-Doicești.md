```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ROU-04366-04145") and reject-phase = false
sort location, company asc
```
