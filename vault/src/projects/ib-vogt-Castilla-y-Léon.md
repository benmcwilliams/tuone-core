```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-07874-06411") and reject-phase = false
sort location, company asc
```
