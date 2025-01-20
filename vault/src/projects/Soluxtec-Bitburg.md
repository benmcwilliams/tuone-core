```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "DEU-03220-03523") and reject-phase = false
sort location, company asc
```
