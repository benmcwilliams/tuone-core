```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NOR-02726-02580") and reject-phase = false
sort location, company asc
```
