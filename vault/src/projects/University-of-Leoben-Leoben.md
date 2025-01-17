```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "AUT-00632-00803") and reject-phase = false
sort location, company asc
```
