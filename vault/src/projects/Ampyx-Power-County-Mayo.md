```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "IRL-06171-06730") and reject-phase = false
sort location, company asc
```
