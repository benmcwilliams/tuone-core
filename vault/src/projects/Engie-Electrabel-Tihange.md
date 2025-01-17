```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BEL-08686-08815") and reject-phase = false
sort location, company asc
```
