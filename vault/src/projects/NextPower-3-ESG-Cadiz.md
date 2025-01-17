```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-03619-07954") and reject-phase = false
sort location, company asc
```
