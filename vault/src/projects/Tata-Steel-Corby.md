```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-08483-06195") and reject-phase = false
sort location, company asc
```
