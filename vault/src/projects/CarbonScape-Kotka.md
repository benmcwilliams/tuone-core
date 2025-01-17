```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-00597-07252") and reject-phase = false
sort location, company asc
```
