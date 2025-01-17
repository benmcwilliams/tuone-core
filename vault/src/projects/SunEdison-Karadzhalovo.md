```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-06127-03548") and reject-phase = false
sort location, company asc
```
