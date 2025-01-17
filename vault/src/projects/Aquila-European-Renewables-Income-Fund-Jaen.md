```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-06924-07569") and reject-phase = false
sort location, company asc
```
