```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-07313-06882") and reject-phase = false
sort location, company asc
```
