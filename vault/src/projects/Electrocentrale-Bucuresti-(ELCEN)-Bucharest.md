```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "ROU-04451-04912") and reject-phase = false
sort location, company asc
```
