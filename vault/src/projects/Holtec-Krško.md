```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "SVN-08390-09148") and reject-phase = false
sort location, company asc
```
