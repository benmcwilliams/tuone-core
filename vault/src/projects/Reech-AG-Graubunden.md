```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "CHE-03682-04213") and reject-phase = false
sort location, company asc
```
