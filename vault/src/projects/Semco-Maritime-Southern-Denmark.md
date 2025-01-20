```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "DNK-08171-09985") and reject-phase = false
sort location, company asc
```
