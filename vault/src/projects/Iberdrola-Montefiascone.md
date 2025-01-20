```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "ITA-04905-01118") and reject-phase = false
sort location, company asc
```
