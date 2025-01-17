```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-07535-07904") and reject-phase = false
sort location, company asc
```
