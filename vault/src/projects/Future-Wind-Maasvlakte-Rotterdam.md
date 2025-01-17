```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-08828-08934") and reject-phase = false
sort location, company asc
```
