```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "AUT-00640-06421") and reject-phase = false
sort location, company asc
```
