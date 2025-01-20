```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "FIN-08088-05228") and reject-phase = false
sort location, company asc
```
