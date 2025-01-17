```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "AUT-00388-01319") and reject-phase = false
sort location, company asc
```
