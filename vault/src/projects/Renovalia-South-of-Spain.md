```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-05472-05913") and reject-phase = false
sort location, company asc
```
