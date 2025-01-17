```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NOR-01515-09193") and reject-phase = false
sort location, company asc
```
