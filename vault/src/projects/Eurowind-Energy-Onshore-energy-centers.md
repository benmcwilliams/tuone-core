```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DNK-05948-02226") and reject-phase = false
sort location, company asc
```
