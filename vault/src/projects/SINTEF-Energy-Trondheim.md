```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NOR-02183-09906") and reject-phase = false
sort location, company asc
```
