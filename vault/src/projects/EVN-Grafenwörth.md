```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "AUT-04105-04884") and reject-phase = false
sort location, company asc
```
