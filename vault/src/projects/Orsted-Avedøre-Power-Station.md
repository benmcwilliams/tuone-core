```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DNK-06416-01842") and reject-phase = false
sort location, company asc
```
