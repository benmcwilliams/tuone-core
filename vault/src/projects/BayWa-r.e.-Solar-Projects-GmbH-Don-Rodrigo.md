```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-07003-07603") and reject-phase = false
sort location, company asc
```
