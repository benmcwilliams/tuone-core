```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "BEL-06712-02141") and reject-phase = false
sort location, company asc
```
