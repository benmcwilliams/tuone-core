```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "EST-08520-06473") and reject-phase = false
sort location, company asc
```
