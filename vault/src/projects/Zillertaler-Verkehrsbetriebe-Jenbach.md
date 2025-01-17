```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "AUT-04753-06400") and reject-phase = false
sort location, company asc
```
