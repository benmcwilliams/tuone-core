```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CHE-01977-01808") and reject-phase = false
sort location, company asc
```
