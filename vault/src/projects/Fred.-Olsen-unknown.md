```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NOR-01316-08922") and reject-phase = false
sort location, company asc
```
