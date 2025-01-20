```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "DNK-09149-09225") and reject-phase = false
sort location, company asc
```
