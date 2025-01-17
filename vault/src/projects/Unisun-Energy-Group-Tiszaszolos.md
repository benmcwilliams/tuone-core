```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HUN-10141-10286") and reject-phase = false
sort location, company asc
```
