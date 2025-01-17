```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-01800-01839") and reject-phase = false
sort location, company asc
```
