```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CHE-07966-08739") and reject-phase = false
sort location, company asc
```
