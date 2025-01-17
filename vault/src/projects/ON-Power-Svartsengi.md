```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ISL-04202-09622") and reject-phase = false
sort location, company asc
```
