```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "ITA-06773-00006") and reject-phase = false
sort location, company asc
```
