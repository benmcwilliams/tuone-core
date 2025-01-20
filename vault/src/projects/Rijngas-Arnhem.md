```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "NLD-02787-05921") and reject-phase = false
sort location, company asc
```
