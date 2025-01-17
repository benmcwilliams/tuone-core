```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SVN-08390-05465") and reject-phase = false
sort location, company asc
```
