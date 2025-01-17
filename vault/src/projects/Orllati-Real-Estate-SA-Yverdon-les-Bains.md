```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CHE-01487-09662") and reject-phase = false
sort location, company asc
```
