```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ESP-00068-06280") and reject-phase = false
sort location, company asc
```
