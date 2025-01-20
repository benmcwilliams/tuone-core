```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "SVK-10161-10326") and reject-phase = false
sort location, company asc
```
