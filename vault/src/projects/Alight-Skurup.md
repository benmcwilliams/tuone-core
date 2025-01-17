```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-03959-02628") and reject-phase = false
sort location, company asc
```
