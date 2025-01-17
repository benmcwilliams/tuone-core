```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SVN-00815-00521") and reject-phase = false
sort location, company asc
```
