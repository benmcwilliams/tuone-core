```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "EST-08593-07741") and reject-phase = false
sort location, company asc
```
