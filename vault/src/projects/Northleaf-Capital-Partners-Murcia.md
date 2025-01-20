```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "ESP-04906-07958") and reject-phase = false
sort location, company asc
```
