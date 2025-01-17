```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CHE-09384-03196") and reject-phase = false
sort location, company asc
```
