```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-08943-09062") and reject-phase = false
sort location, company asc
```
