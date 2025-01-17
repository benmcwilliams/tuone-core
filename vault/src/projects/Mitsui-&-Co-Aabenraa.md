```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DNK-04576-04105") and reject-phase = false
sort location, company asc
```
