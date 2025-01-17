```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-00870-00278") and reject-phase = false
sort location, company asc
```
