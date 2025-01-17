```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-02038-01830") and reject-phase = false
sort location, company asc
```
