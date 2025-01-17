```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-06996-07597") and reject-phase = false
sort location, company asc
```
