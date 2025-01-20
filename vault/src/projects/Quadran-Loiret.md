```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "FRA-06231-05868") and reject-phase = false
sort location, company asc
```
