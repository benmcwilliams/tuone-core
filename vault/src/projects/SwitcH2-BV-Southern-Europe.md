```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-06995-08106") and reject-phase = false
sort location, company asc
```
