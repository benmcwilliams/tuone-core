```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NOR-05985-06539") and reject-phase = false
sort location, company asc
```
