```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "NOR-09732-07361") and reject-phase = false
sort location, company asc
```
