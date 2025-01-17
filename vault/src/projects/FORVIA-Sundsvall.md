```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-08617-06885") and reject-phase = false
sort location, company asc
```
