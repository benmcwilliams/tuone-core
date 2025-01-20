```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "POL-02664-03302") and reject-phase = false
sort location, company asc
```
