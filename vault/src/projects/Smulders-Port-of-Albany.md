```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BEL-09987-08068") and reject-phase = false
sort location, company asc
```
