```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "HRV-08982-02971") and reject-phase = false
sort location, company asc
```
