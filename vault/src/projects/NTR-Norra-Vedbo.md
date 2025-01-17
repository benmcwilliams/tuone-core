```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-09437-05639") and reject-phase = false
sort location, company asc
```
