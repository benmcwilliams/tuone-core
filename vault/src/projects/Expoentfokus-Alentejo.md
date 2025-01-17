```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "PRT-06965-07775") and reject-phase = false
sort location, company asc
```
