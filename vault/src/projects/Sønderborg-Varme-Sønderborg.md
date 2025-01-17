```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DNK-09150-10178") and reject-phase = false
sort location, company asc
```
