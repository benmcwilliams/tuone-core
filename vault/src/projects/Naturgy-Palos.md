```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-05208-01205") and reject-phase = false
sort location, company asc
```
