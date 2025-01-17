```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HUN-08291-08523") and reject-phase = false
sort location, company asc
```
