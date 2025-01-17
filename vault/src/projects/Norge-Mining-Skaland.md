```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NOR-06718-07322") and reject-phase = false
sort location, company asc
```
