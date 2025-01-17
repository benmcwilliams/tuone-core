```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-02178-02559") and reject-phase = false
sort location, company asc
```
