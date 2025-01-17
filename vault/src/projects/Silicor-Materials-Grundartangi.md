```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ISL-09975-10010") and reject-phase = false
sort location, company asc
```
