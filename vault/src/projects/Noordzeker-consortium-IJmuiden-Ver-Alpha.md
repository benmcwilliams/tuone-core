```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-09482-09565") and reject-phase = false
sort location, company asc
```
