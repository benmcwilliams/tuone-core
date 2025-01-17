```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HRV-09300-09417") and reject-phase = false
sort location, company asc
```
