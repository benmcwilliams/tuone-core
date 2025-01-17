```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CZE-06236-00597") and reject-phase = false
sort location, company asc
```
