```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NOR-07893-03250") and reject-phase = false
sort location, company asc
```
