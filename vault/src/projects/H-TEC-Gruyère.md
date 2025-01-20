```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "CHE-05968-02263") and reject-phase = false
sort location, company asc
```
