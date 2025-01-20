```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "FIN-00462-02263") and reject-phase = false
sort location, company asc
```
