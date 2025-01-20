```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "FRA-04415-04875") and reject-phase = false
sort location, company asc
```
