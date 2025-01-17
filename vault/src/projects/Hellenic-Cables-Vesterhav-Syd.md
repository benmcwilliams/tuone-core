```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DNK-09033-09131") and reject-phase = false
sort location, company asc
```
