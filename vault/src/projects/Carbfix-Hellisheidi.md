```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ISL-08274-08502") and reject-phase = false
sort location, company asc
```
