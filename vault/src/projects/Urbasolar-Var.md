```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-07618-03685") and reject-phase = false
sort location, company asc
```
