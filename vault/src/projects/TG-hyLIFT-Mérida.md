```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-05279-08110") and reject-phase = false
sort location, company asc
```
