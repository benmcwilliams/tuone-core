```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "EST-08590-07741") and reject-phase = false
sort location, company asc
```
