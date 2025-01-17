```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-03406-05813") and reject-phase = false
sort location, company asc
```
