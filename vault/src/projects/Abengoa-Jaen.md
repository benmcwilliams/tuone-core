```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "ESP-06924-04432") and reject-phase = false
sort location, company asc
```
