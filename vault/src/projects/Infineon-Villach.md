```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "AUT-04951-00387") and reject-phase = false
sort location, company asc
```
