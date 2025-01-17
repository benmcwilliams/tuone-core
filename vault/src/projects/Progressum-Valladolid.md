```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-01180-07996") and reject-phase = false
sort location, company asc
```
