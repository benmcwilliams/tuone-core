```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-03534-06433") and reject-phase = false
sort location, company asc
```
