```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "ESP-01000-06427") and reject-phase = false
sort location, company asc
```
