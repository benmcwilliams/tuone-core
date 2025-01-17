```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SVK-02397-02430") and reject-phase = false
sort location, company asc
```
