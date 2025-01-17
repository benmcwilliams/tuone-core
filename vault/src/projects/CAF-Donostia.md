```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-00270-00117") and reject-phase = false
sort location, company asc
```
