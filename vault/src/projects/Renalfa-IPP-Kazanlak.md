```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "BGR-07967-01890") and reject-phase = false
sort location, company asc
```
