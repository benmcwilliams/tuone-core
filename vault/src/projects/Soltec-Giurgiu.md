```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ROU-09402-03520") and reject-phase = false
sort location, company asc
```
