```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-02469-04937") and reject-phase = false
sort location, company asc
```
