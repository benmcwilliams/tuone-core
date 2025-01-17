```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-03301-02116") and reject-phase = false
sort location, company asc
```
