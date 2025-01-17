```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HUN-00249-08555") and reject-phase = false
sort location, company asc
```
