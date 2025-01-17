```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-05135-01671") and reject-phase = false
sort location, company asc
```
