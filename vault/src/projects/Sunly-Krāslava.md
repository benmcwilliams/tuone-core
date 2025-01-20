```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "LVA-10055-10149") and reject-phase = false
sort location, company asc
```
