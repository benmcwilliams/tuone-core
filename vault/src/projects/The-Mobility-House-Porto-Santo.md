```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "PRT-07802-01331") and reject-phase = false
sort location, company asc
```
