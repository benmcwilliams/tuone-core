```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-02192-10190") and reject-phase = false
sort location, company asc
```
