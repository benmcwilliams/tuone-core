```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ITA-00172-07384") and reject-phase = false
sort location, company asc
```
