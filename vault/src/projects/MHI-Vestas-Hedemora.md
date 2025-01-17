```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-09310-02352") and reject-phase = false
sort location, company asc
```
