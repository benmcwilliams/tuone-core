```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "AUT-00388-00273") and reject-phase = false
sort location, company asc
```
