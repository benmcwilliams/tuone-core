```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "IRL-01933-02033") and reject-phase = false
sort location, company asc
```
