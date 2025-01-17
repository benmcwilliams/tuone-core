```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BEL-08552-08753") and reject-phase = false
sort location, company asc
```
