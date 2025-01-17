```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-07000-03108") and reject-phase = false
sort location, company asc
```
