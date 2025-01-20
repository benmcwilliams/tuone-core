```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "SWE-10251-10393") and reject-phase = false
sort location, company asc
```
