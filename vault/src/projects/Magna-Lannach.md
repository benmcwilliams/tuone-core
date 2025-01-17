```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "AUT-05101-00496") and reject-phase = false
sort location, company asc
```
