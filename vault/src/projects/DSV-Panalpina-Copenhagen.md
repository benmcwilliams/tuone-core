```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "DNK-00220-03883") and reject-phase = false
sort location, company asc
```
