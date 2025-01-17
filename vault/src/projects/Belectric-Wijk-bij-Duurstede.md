```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-04056-00096") and reject-phase = false
sort location, company asc
```
