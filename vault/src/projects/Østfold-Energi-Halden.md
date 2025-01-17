```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NOR-07972-10493") and reject-phase = false
sort location, company asc
```
