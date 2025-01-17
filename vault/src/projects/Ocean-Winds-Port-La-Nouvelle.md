```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FRA-07557-07963") and reject-phase = false
sort location, company asc
```
