```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-00765-02652") and reject-phase = false
sort location, company asc
```
