```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DNK-08016-08310") and reject-phase = false
sort location, company asc
```
