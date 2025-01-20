```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "DEU-03970-00182") and reject-phase = false
sort location, company asc
```
