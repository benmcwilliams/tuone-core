```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-03737-04282") and reject-phase = false
sort location, company asc
```
