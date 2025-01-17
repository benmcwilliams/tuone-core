```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "IRL-03966-04489") and reject-phase = false
sort location, company asc
```
