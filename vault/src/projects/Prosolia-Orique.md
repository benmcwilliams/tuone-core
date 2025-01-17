```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "PRT-07666-08001") and reject-phase = false
sort location, company asc
```
