```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "AUT-04308-00156") and reject-phase = false
sort location, company asc
```
