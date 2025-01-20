```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "CZE-00588-00782") and reject-phase = false
sort location, company asc
```
