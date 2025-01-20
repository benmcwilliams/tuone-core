```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "NOR-04097-02437") and reject-phase = false
sort location, company asc
```
