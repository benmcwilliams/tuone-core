```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "SWE-08078-08364") and reject-phase = false
sort location, company asc
```
