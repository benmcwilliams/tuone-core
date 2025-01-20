```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "SWE-00386-10367") and reject-phase = false
sort location, company asc
```
