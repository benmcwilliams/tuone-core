```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-07391-08112") and reject-phase = false
sort location, company asc
```
