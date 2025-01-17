```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "AUT-09233-09323") and reject-phase = false
sort location, company asc
```
