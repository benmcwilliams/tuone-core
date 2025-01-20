```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "NOR-09353-02355") and reject-phase = false
sort location, company asc
```
