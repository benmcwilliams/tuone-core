```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "IRL-05147-05572") and reject-phase = false
sort location, company asc
```
