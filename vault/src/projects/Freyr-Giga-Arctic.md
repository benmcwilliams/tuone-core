```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NOR-00368-00296") and reject-phase = false
sort location, company asc
```
