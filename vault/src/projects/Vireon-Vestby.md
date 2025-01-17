```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NOR-05787-06318") and reject-phase = false
sort location, company asc
```
