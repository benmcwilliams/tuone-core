```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "BEL-02668-05621") and reject-phase = false
sort location, company asc
```
