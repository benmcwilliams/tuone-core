```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-08727-09674") and reject-phase = false
sort location, company asc
```
