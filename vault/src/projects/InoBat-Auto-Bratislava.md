```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SVK-00120-00391") and reject-phase = false
sort location, company asc
```
