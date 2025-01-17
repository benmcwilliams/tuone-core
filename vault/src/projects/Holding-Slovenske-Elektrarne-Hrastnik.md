```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SVN-04806-06958") and reject-phase = false
sort location, company asc
```
