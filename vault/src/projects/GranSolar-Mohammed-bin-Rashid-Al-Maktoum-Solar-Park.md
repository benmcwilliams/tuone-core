```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-01611-06916") and reject-phase = false
sort location, company asc
```
