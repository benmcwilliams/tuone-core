```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-04056-01776") and reject-phase = false
sort location, company asc
```
