```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "ESP-07711-08029") and reject-phase = false
sort location, company asc
```
