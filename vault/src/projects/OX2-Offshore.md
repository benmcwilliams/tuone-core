```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "SWE-02274-01836") and reject-phase = false
sort location, company asc
```
