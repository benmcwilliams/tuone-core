```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NOR-02350-08755") and reject-phase = false
sort location, company asc
```
