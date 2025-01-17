```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "EST-08756-07933") and reject-phase = false
sort location, company asc
```
