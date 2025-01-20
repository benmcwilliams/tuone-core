```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "SVK-09189-09276") and reject-phase = false
sort location, company asc
```
