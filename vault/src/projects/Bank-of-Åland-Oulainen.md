```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-08089-08374") and reject-phase = false
sort location, company asc
```
