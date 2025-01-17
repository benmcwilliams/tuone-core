```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-10049-10138") and reject-phase = false
sort location, company asc
```
