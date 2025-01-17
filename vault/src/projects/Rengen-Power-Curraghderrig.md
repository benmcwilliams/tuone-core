```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "IRL-08608-09857") and reject-phase = false
sort location, company asc
```
