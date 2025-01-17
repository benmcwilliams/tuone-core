```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DNK-02098-09171") and reject-phase = false
sort location, company asc
```
