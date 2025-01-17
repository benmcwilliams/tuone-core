```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-06320-08781") and reject-phase = false
sort location, company asc
```
