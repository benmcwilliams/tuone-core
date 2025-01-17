```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "IRL-08487-01592") and reject-phase = false
sort location, company asc
```
