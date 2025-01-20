```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "CHE-09443-09536") and reject-phase = false
sort location, company asc
```
