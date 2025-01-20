```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "CHE-10234-10364") and reject-phase = false
sort location, company asc
```
