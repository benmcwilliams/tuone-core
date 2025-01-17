```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-09219-09306") and reject-phase = false
sort location, company asc
```
