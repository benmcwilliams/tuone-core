```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HRV-08890-08986") and reject-phase = false
sort location, company asc
```
