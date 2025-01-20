```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "ESP-06991-07638") and reject-phase = false
sort location, company asc
```
