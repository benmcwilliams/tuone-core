```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HUN-08693-08821") and reject-phase = false
sort location, company asc
```
