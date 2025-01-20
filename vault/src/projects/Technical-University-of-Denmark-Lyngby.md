```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "DNK-03270-03607") and reject-phase = false
sort location, company asc
```
