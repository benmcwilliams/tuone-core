```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "POL-06344-01636") and reject-phase = false
sort location, company asc
```
