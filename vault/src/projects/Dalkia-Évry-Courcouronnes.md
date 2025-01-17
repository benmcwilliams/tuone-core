```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-07108-07671") and reject-phase = false
sort location, company asc
```
