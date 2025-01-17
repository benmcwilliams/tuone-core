```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-09811-09835") and reject-phase = false
sort location, company asc
```
