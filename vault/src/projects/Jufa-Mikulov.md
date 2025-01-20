```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "CZE-09214-09300") and reject-phase = false
sort location, company asc
```
