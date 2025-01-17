```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "PRT-02653-07841") and reject-phase = false
sort location, company asc
```
