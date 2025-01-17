```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-03816-00006") and reject-phase = false
sort location, company asc
```
