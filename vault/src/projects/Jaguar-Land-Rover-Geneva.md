```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CHE-00361-00412") and reject-phase = false
sort location, company asc
```
